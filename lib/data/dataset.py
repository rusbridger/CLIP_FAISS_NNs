from lib.hparams import collection_images, collection_text, n_components

from faiss import read_index
from json import load
from os import listdir
from os.path import exists
import torchvision


def load_images(dataset_path):
    return torchvision.datasets.ImageFolder(dataset_path)


def load_text(data):
    keys = set()

    def unpack_keys(curr_data, main=None):
        for (key, value) in curr_data.items():
            keys.add("a picture of {}".format(key))
            unpack_keys(value, main=key)

    unpack_keys(data)
    return sorted(keys)


def build_img_repo_map():
    repos = dict()

    for repo in sorted(collection_images):
        repo_name, repo_path = repo[0], repo[1]
        index_path = "indexes_images/{}_{}.index".format(
            repo_name, n_components)

        if exists(index_path) and exists(repo_path):
            dataset = load_images(repo_path)
            repos[repo_name] = dataset

    return repos


def build_txt_repo_map():
    repos = dict()

    for repo in sorted(collection_text):
        repo_name, repo_path = repo[0], repo[1]
        index_path = "indexes_text/{}_{}.index".format(repo_name, n_components)

        if exists(index_path) and exists(repo_path):
            with open(repo_path) as fp:
                data = load(fp)
            dataset = load_text(data)
            repos[repo_name] = dataset

    return repos


def build_img_data_subset(datasets, repos):
    subsets = []
    subset_size = 0
    for r in repos:
        subsets.append(datasets[r])
        subset_size += len(datasets[r])

    return subsets, subset_size


def index_into_subsets(subsets, index):
    curr_idx = 0
    for ss in subsets:
        if curr_idx + len(ss) >= index:
            return ss.imgs[index - curr_idx][0]
        curr_idx += len(ss)

    return None
