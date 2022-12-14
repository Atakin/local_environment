import math
import os
from rdkit import Chem
from settings import H_BONDS
from rdkit.Chem.rdchem import BondType
from rdkit.Geometry import Point3D
import shutil


def get_local_environments(filepath, r_cut):
    dir_path = _make_dir_to_submols(filepath)
    mol = _upload_mol_from_mol_file(filepath)
    submols, atom_map = get_submols(mol, r_cut)
    _write_submols_to_files(submols, dir_path)
    _write_atom_map_to_file(atom_map, dir_path)
    _put_main_atom_on_first_place(atom_map, dir_path)


def get_submols(mol, radius):
    atom_map = []
    atoms = mol.GetAtoms()
    submols = []
    for atom in atoms:
        env = Chem.rdmolops.FindAtomEnvironmentOfRadiusN(
            mol, radius, atom.GetIdx(), useHs=True
        )
        amap = {}
        submol = Chem.RWMol(Chem.PathToSubmol(mol, env, atomMap=amap))
        atom_map.append((atom.GetIdx() + 1, amap[atom.GetIdx()] + 1))
        check_and_repair_submol(submol, mol, amap)
        submols.append(submol)
    return submols, atom_map


def get_coords(mol, atom_idx):
    return mol.GetConformer().GetAtomPosition(atom_idx)


def set_coords(mol, atom_idx, point):
    mol.GetConformer().SetAtomPosition(atom_idx, point)


def check_and_repair_submol(submol, mol, amap):
    restore_rings(submol, mol, amap)
    bad_atoms = find_bad_atoms(submol, mol, amap)
    for submol_atom, mol_atom in bad_atoms:
        repair_atom(submol_atom, mol_atom, submol, mol)


def restore_rings(submol, mol, amap):
    ssr = Chem.GetSymmSSSR(mol)
    for ring in ssr:
        ring_atmos = list(ring)
        if need_to_restore_ring(ring_atmos, amap):
            restore_ring(submol, mol, amap, ring_atmos)


def need_to_restore_ring(ring_atmos, amap):
    if len(ring_atmos) > 6:
        return False
    atoms_from_ring = 0
    for atom in amap:
        if atom in ring_atmos:
            atoms_from_ring += 1
    return atoms_from_ring > 1


def restore_ring(submol, mol, amap, ring_atoms):
    atoms_to_add = []
    for ring_atom in ring_atoms:
        if ring_atom not in amap:
            atoms_to_add.append(ring_atom)

    for atom in atoms_to_add:
        new_atom = Chem.Atom(mol.GetAtomWithIdx(atom).GetSymbol())
        new_atom_idx = submol.AddAtom(new_atom)
        amap[atom] = new_atom_idx
        set_coords(submol, new_atom_idx, get_coords(mol, atom))

    for atom in atoms_to_add:
        neibs = mol.GetAtomWithIdx(atom).GetNeighbors()
        for neib in neibs:
            neib_idx = neib.GetIdx()
            if (
                neib_idx in ring_atoms
                and submol.GetBondBetweenAtoms(amap[neib_idx], amap[atom]) is None
            ):
                bond_type = mol.GetBondBetweenAtoms(neib_idx, atom).GetBondType()
                submol.AddBond(amap[neib.GetIdx()], amap[atom], bond_type)


def repair_atom(submol_atom, mol_atom, submol, mol):
    missing_atoms = find_missing_atoms(submol_atom, mol_atom, submol, mol)
    missing_atoms = try_to_find_missing_atom_in_submol(
        submol_atom, mol_atom, submol, mol, missing_atoms
    )
    if is_bonds_single(missing_atoms, mol, mol_atom):
        for missing_atom in missing_atoms:
            add_atom_H(missing_atom, submol_atom, mol_atom, submol, mol)
    else:
        try_change_r_cut(missing_atoms, submol_atom, mol_atom, submol, mol)


def try_to_find_missing_atom_in_submol(
    submol_atom, mol_atom, submol, mol, missing_atoms
):
    cleared_missing_atoms = []
    for missing_atom in missing_atoms:
        cleared = True
        for submol_another_atom in submol.GetAtoms():
            if get_atom_tupple(mol, missing_atom.GetIdx()) == get_atom_tupple(
                submol, submol_another_atom.GetIdx()
            ):
                cleared = False
                restore_bond(
                    submol_atom, submol_another_atom, missing_atom, submol, mol
                )
        if cleared:
            cleared_missing_atoms.append(missing_atom)
    return cleared_missing_atoms


def restore_bond(submol_atom, submol_another_atom, missing_atom, submol, mol):
    for neib in missing_atom.GetNeighbors():
        if get_atom_tupple(mol, neib.GetIdx()) == get_atom_tupple(
            submol, submol_atom.GetIdx()
        ):
            bond_type = mol.GetBondBetweenAtoms(
                missing_atom.GetIdx(), neib.GetIdx()
            ).GetBondType()
            submol.AddBond(
                submol_atom.GetIdx(), submol_another_atom.GetIdx(), bond_type
            )


def count_Hs(atoms):
    result = 0
    for atom in atoms:
        if atom.GetSymbol() == "H":
            result += 1
    return result


def add_atom_H(atom_to_add_on, submol_atom, mol_atom, submol, mol):
    if atom_to_add_on.GetSymbol() == "H":
        coords = get_coords(mol, atom_to_add_on.GetIdx())
        insert_atom(submol, submol_atom, "H", coords, BondType.SINGLE)
    else:
        coords = calculate_coords(mol, mol_atom, atom_to_add_on)
        insert_atom(submol, submol_atom, "H", coords, BondType.SINGLE)


def calculate_coords(mol, mol_atom, atom_to_add_on):
    bond_length = H_BONDS.get(mol_atom.GetSymbol())
    if bond_length is None:
        raise ValueError(f"Unsupperted atom {mol_atom.GetSymbol()}")

    mol_atom_coords = get_coords(mol, mol_atom.GetIdx())
    atom_to_add_on_coords = get_coords(mol, atom_to_add_on.GetIdx())
    vector = [
        atom_to_add_on_coords.x - mol_atom_coords.x,
        atom_to_add_on_coords.y - mol_atom_coords.y,
        atom_to_add_on_coords.z - mol_atom_coords.z,
    ]
    vector_module = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
    ort = [coord / vector_module for coord in vector]
    coords = Point3D(
        mol_atom_coords.x + ort[0] * bond_length,
        mol_atom_coords.y + ort[1] * bond_length,
        mol_atom_coords.z + ort[2] * bond_length,
    )
    return coords


def insert_atom(mol, to_atom, symbol, coords, bond_type):
    new_atom = Chem.Atom(symbol)
    new_atom_idx = mol.AddAtom(new_atom)
    mol.AddBond(to_atom.GetIdx(), new_atom_idx, bond_type)
    set_coords(mol, new_atom_idx, coords)
    return new_atom_idx


def is_bonds_single(missing_atoms, mol, mol_atom):
    for atom in missing_atoms:
        if (
            mol.GetBondBetweenAtoms(mol_atom.GetIdx(), atom.GetIdx()).GetBondType()
            != BondType.SINGLE
        ):
            return False
    return True


def is_bond_single(mol, atom_idx_1, atom_idx_2):
    return (
        mol.GetBondBetweenAtoms(atom_idx_1, atom_idx_2).GetBondType() == BondType.SINGLE
    )


def try_change_r_cut(missing_atoms, submol_atom, mol_atom, submol, mol):
    can_add = True
    to_add = []
    for missing_atom in missing_atoms:
        if not is_bond_single(mol, mol_atom.GetIdx(), missing_atom.GetIdx()):
            missing_atom_neibs = []
            for atom in missing_atom.GetNeighbors():
                if get_atom_tupple(mol, atom.GetIdx()) != get_atom_tupple(
                    mol, mol_atom.GetIdx()
                ):
                    missing_atom_neibs.append(atom)

            if len(missing_atom_neibs) == 0:
                to_add.append([("original", missing_atom, mol_atom)])
            else:
                if is_bonds_single(missing_atom_neibs, mol, missing_atom):
                    to_add_new = [("original", missing_atom, mol_atom)]
                    for neib in missing_atom_neibs:
                        to_add_new.append(("H", neib, missing_atom))
                    to_add.append(to_add_new)
                else:
                    can_add = False
        else:
            to_add.append([("H", missing_atom, mol_atom)])
    if can_add:
        for add in to_add:
            if len(add) == 1:
                add = add[0]
                if add[0] == "original":
                    insert_atom(
                        submol,
                        submol_atom,
                        add[1].GetSymbol(),
                        get_coords(mol, add[1].GetIdx()),
                        mol.GetBondBetweenAtoms(
                            add[1].GetIdx(), add[2].GetIdx()
                        ).GetBondType(),
                    )
                elif add[0] == "H":
                    insert_atom(
                        submol,
                        submol_atom,
                        "H",
                        calculate_coords(mol, add[2], add[1]),
                        BondType.SINGLE,
                    )
            else:
                new_idx = insert_atom(
                    submol,
                    submol_atom,
                    add[0][1].GetSymbol(),
                    get_coords(mol, add[0][1].GetIdx()),
                    mol.GetBondBetweenAtoms(
                        add[0][1].GetIdx(), add[0][2].GetIdx()
                    ).GetBondType(),
                )
                for atom_to_add in add[1:]:
                    if atom_to_add[0] == "original":
                        insert_atom(
                            submol,
                            submol.GetAtomWithIdx(new_idx),
                            atom_to_add[1].GetSymbol(),
                            get_coords(mol, atom_to_add[1].GetIdx()),
                            mol.GetBondBetweenAtoms(
                                atom_to_add[1].GetIdx(), atom_to_add[2].GetIdx()
                            ).GetBondType(),
                        )
                    elif atom_to_add[0] == "H":
                        insert_atom(
                            submol,
                            submol.GetAtomWithIdx(new_idx),
                            "H",
                            calculate_coords(mol, atom_to_add[2], atom_to_add[1]),
                            BondType.SINGLE,
                        )
    else:
        print(
            f"Error for atom {mol_atom.GetSymbol()} with number {mol_atom.GetIdx()+1}"
        )


def find_missing_atoms(submol_atom, mol_atom, submol, mol):
    mol_atom_neibs = mol_atom.GetNeighbors()
    missing_atoms = []
    submol_atom_neibs_set = get_neibs_set(submol_atom, submol)
    for mol_neib in mol_atom_neibs:
        coords = get_coords(mol, mol_neib.GetIdx())
        if (
            mol_neib.GetSymbol(),
            coords.x,
            coords.y,
            coords.z,
        ) not in submol_atom_neibs_set:
            missing_atoms.append(mol_neib)
    return missing_atoms


def get_neibs_set(atom, mol):
    result = set()
    atom_neibs = atom.GetNeighbors()
    for neib in atom_neibs:
        coords = get_coords(mol, neib.GetIdx())
        result.add((neib.GetSymbol(), coords.x, coords.y, coords.z))
    return result


def find_bad_atoms(submol, mol, amap):
    bad_atoms = []
    mol_atoms = mol.GetAtoms()
    for mol_atom in mol_atoms:
        mol_atom_id = mol_atom.GetIdx()
        if mol_atom_id not in amap:
            continue
        submol_atom = submol.GetAtomWithIdx(amap[mol_atom_id])
        if len(mol_atom.GetNeighbors()) > len(submol_atom.GetNeighbors()):
            bad_atoms.append((submol_atom, mol_atom))
    return bad_atoms


def get_atom_tupple(mol, atom_idx):
    coords = get_coords(mol, atom_idx)
    return (mol.GetAtomWithIdx(atom_idx).GetSymbol(), coords.x, coords.y, coords.z)


def _upload_mol_from_mol_file(filepath):
    mol = Chem.MolFromMolFile(filepath, removeHs=False)
    Chem.Kekulize(mol, clearAromaticFlags=True)
    return mol


def _write_submols_to_files(submols, dir_path):
    for i, submol in enumerate(submols):
        print(
            Chem.MolToMolBlock(submol),
            file=open(dir_path + f"/{i + 1}.mol", "w+"),
        )
        print(
            Chem.MolToXYZBlock(submol),
            file=open(dir_path + f"/{i + 1}.xyz", "w+"),
        )


def _make_dir_to_submols(filepath):
    full_name = os.path.basename(filepath)
    ext = os.path.splitext(full_name)[1]
    dir_path = filepath.replace(ext, "")
    dir_path += "_submols"
    _create_mol_dir(dir_path)
    return dir_path


def _write_atom_map_to_file(atom_map, dir_path):
    with open(dir_path + "/atom_map.txt", "w+") as f:
        for atom in atom_map:
            f.write(f"{atom[0]} -> {atom[1]}\n")


def _put_main_atom_on_first_place(atom_map, dir_path):
    new_dir_path = dir_path + "_xyz"
    _create_mol_dir(new_dir_path)
    for mol_idx, submol_idx in atom_map:
        with open(dir_path + f"/{mol_idx}.xyz", "r") as rf:
            with open(new_dir_path + f"/{mol_idx}.xyz", "w+") as wf:
                lines = rf.read().splitlines(keepends=True)
                lines[2], lines[submol_idx + 1] = lines[submol_idx + 1], lines[2]
                wf.writelines(lines)


def _create_mol_dir(dir_path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)
    print("created", dir_path)
