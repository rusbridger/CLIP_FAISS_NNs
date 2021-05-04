from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from json import dump
from os import environ
from random import sample

from lib.data import *
from lib.index.build import build_txt_index_faiss
from lib.index.collection import update_collection_text
from lib.index.query import classify_img, search_sim, search_txt

app = Flask("Multimodal CLIP Application Demo")
CORS(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

img_repos = build_img_repo_map()
txt_repos = build_txt_repo_map()
subset_preview_length = 6


@app.route("/api/hello", methods=["POST"])
def hello():
    print("HELLO")
    return jsonify({}), 200


@app.route("/api/repos/images", methods=["POST"])
def get_img_repos():
    return jsonify({"repos": sorted(list(img_repos.keys()))})


@app.route("/api/repos/text", methods=["POST"])
def get_txt_repos():
    return jsonify({"repos": sorted(list(txt_repos.keys()))})


@app.route("/api/repos/images", methods=["POST"])
def get_imgs():
    data = request.json
    mode = data["mode"]["id"]
    repos = data["repos"]

    subsets, subset_size = build_img_data_subset(img_repos, repos)
    subset_indices = sample(range(subset_size), subset_preview_length)
    filepaths = [(int(i), index_into_subsets(subsets, i))
                 for i in subset_indices]

    return jsonify({"filepaths": filepaths})


@app.route("/api/classify", methods=["POST"])
def classify():
    data = request.json
    repos = data["repos"]
    txt_repos = data["txt_repos"]
    index = data["index"]
    nnn = data["n_neighbours"]
    classified = classify_img(repos, txt_repos, index, nnn)

    return jsonify({"classified": classified})


@app.route("/api/search", methods=["POST"])
def search():
    data = request.json
    repos = data["repos"]
    query = "a picture of {}".format(data["query"])
    nnn = data["n_neighbours"]

    subsets = build_img_data_subset(img_repos, repos)
    result_indices = search_txt(repos, query, nnn)
    filepaths = [(int(i), index_into_subsets(subsets, i))
                 for i in result_indices]

    return jsonify({"filepaths": filepaths})


@app.route("/api/similar", methods=["POST"])
def similar():
    data = request.json
    repos = data["repos"]
    index = data["index"]
    nnn = data["n_neighbours"]

    subsets = build_img_data_subset(img_repos, repos)
    result_indices = search_sim(repos, index, nnn)
    filepaths = [(int(i), index_into_subsets(subsets, i))
                 for i in result_indices]

    return jsonify({"filepaths": filepaths})


@app.route("/api/repos/text/add", methods=["POST"])
def add_text_repo():
    if "BLOCKING" not in environ:
        return jsonify({}), 403

    data = request.json
    name, vocab = data["name"], data["vocab"]

    text_values = load_text(vocab)

    build_txt_index_faiss(name,
                          text_values,
                          n_components=n_components,
                          verbose=True)

    filepath = "vocab/{}.json".format(name)
    update_collection_text(name, filepath)
    with open(filepath, "w") as outfile:
        dump(vocab, outfile)

    return jsonify({"filepaths": [filepath], "vocab_size": len(text_values)})
