# 概要

## 目的

カオス現象を示す簡単なモデル「Lorenz63 model」を用いて，データ同化について学び体験すること．

## Information

簡単な説明（Lorenz63 modelやデータ同化についてなど）を[docs](./docs/)フォルダにまとめている．

## Setup for Docker

1. Install docker and confirm that `docker compose` command works
2. Modify [docker-compose.yml](./docker-compose.yml) (change port number in pytorch_es to the number assigned to you)
3. Build a container: `$ docker compose build`
4. Start a contaner:
    1. CPU environment: `$ docker compose up -d pytorch_cpu`
    2. GPU environment: `$ docker compose up -d pytorch_gpu`

## Project Organization

    ├── README.md
    ├── docker
    │   ├── pytorch_cpu : CPU環境でのdockerコンテナに関わるディレクトリ
    │   ├── pytorch_gpu : GPUが利用可能な環境でのdockerコンテナに関わるディレクトリ
    ├── docker-compose.yml
    ├── docs
    │   ├── lorenz63_model : Lorenz63 modelに関するドキュメント
    │   └── data_assimilation : データ同化に関するドキュメント
    ├── python
        ├── notebooks
        │   └── lorenz63_model : Lorenz63 modelに関するノートブック
        │   └── data_assimilation : データ同化に関するノートブック
        └── src
            ├── lorenz63_model : Lorenz63 modelに関するコード
            └── data_assimilation : データ同化に関するコード

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
