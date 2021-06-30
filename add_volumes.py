import argparse
import numpy as np
import os
from smpl.smpl_webuser.serialization import load_model
import scipy.io


def main():
    parser = argparse.ArgumentParser(description='Enrich a local copy of the SURREAL dataset with volume information'
                                                 ' and body heights. *_info.mat files must be present.')
    parser.add_argument("-d", "--dataset_path", required=True, help="Path to SURREAL dataset.")
    args = parser.parse_args()

    # get all _info.mat from the dataset
    info_mats = []
    for r, d, f in os.walk(args.dataset_path):
        for file in f:
            if file.endswith("_info.mat"):
                info_mats.append(os.path.join(r, file))

    for i, info_mat in enumerate(info_mats):
        print("Processing *_info.mat {}/{}.".format(i + 1, len(info_mats)))
        infos = scipy.io.loadmat(info_mat)

        part_vols, body_height = calc_vols_and_height(infos['gender'][0][0], infos['shape'][:, 0])
        frame_count = infos['light'].shape[-1]
        infos['part_volumes'] = np.array([part_vols] * frame_count).T
        infos['height'] = np.full(shape=frame_count, fill_value=body_height)

        scipy.io.savemat(info_mat, infos)
    print("done.")


def calc_vols_and_height(gender, shape_params):
    if gender == 0:  # female model
        model = load_model('smpl/models/basicModel_f_lbs_10_207_0_v1.0.0.pkl')
    else:  # male model
        model = load_model('smpl/models/basicModel_m_lbs_10_207_0_v1.0.0.pkl')

    # The coordinates of the vertices are only recalculated if the parameters are assigned to  model.betas[:], not
    # model.betas
    model.pose[:] = np.zeros(model.pose.size)
    model.pose[0] = np.pi
    model.betas[:] = shape_params

    vols = []
    template_path = "templates"
    for i, filename in enumerate(os.listdir(template_path)):
        path = os.path.join(template_path, filename)
        faces = np.load(path).astype(int)
        vols.append(calc_volume(model.a.r, faces - 1))

    height = calc_height(model)

    return vols, height


def calc_height(model):
    return (np.max(model.a.r[:, 1]) - np.min(model.a.r[:, 1])) * 100


def calc_volume(vertices, faces):
    vol = 0.0
    for triangle in faces:
        # Points in mm
        p1 = vertices[triangle[0]] * 1000
        p2 = vertices[triangle[1]] * 1000
        p3 = vertices[triangle[2]] * 1000
        vol += np.inner(
            p1,
            np.cross(p2, p3)
        )
    vol /= 6.0
    # volume: mm^3 --> l = dm^3
    vol = vol / 1e+6
    return vol


if __name__ == "__main__":
    main()
