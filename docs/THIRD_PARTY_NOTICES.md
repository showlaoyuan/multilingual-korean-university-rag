# Third-Party Notices

This project uses third-party software and an externally distributed embedding model. Each component remains governed by its own license and terms. The repository's AGPL-3.0-only license applies only to original project code covered by the project [NOTICE](../NOTICE); it does not relicense the components listed below.

Versions reflect the frozen Python 3.11 experiment environment. The complete installed package list is recorded in [`requirements-lock-py311.txt`](../requirements-lock-py311.txt).

## Direct Software Dependencies

| Component | Version | Use | License | Official source |
| --- | ---: | --- | --- | --- |
| PyMuPDF | 1.28.2 | PDF text extraction | GNU AGPL v3 or Artifex commercial license | [PyMuPDF](https://github.com/pymupdf/PyMuPDF) |
| NumPy | 2.4.6 | Vector storage and similarity computation | BSD-3-Clause and bundled third-party notices | [NumPy](https://github.com/numpy/numpy) |
| pandas | 3.0.5 | Installed analysis dependency | BSD-3-Clause | [pandas](https://github.com/pandas-dev/pandas) |
| tqdm | 4.70.0 | Installed progress/analysis dependency | MPL-2.0 and MIT | [tqdm](https://github.com/tqdm/tqdm) |
| sentence-transformers | 5.7.0 | Embedding model loading and encoding | Apache-2.0 | [Sentence Transformers](https://github.com/huggingface/sentence-transformers) |
| python-dotenv | 1.2.4 | Local environment-variable loading | BSD-3-Clause | [python-dotenv](https://github.com/theskumar/python-dotenv) |
| OpenAI Python client | 3.24.0 | DashScope OpenAI-compatible API client | Apache-2.0 | [OpenAI Python](https://github.com/openai/openai-python) |

## Major Transitive Runtime Dependencies

| Component | Version | License summary | Official source |
| --- | ---: | --- | --- |
| PyTorch | 2.13.0 CPU build | BSD-style license and bundled third-party notices | [PyTorch](https://github.com/pytorch/pytorch) |
| Transformers | 5.15.0 | Apache-2.0 | [Transformers](https://github.com/huggingface/transformers) |
| Hugging Face Hub | 1.27.0 | Apache-2.0 | [Hugging Face Hub](https://github.com/huggingface/huggingface_hub) |
| Tokenizers | 0.22.2 | Apache-2.0 | [Tokenizers](https://github.com/huggingface/tokenizers) |
| scikit-learn | 1.9.0 | BSD-3-Clause | [scikit-learn](https://github.com/scikit-learn/scikit-learn) |
| SciPy | 1.17.1 | BSD-3-Clause and bundled third-party notices | [SciPy](https://github.com/scipy/scipy) |

Installed distributions may contain additional notices for bundled components. Their included license files and upstream repositories remain authoritative.

## Embedding Model

The project uses [`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2), whose model card identifies the license as Apache-2.0. The frozen experiments used model revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`.

Model and tokenizer files are not distributed in the public repository. Users obtain them from the model provider under the provider's license and terms.

## External Generation Service

Answer generation uses `qwen3.7-plus` through the DashScope OpenAI-compatible API. This repository does not distribute Qwen model weights or grant rights to the model or service. API use requires a user-supplied credential and remains subject to the provider's current service terms. See [Alibaba Cloud Model Studio documentation](https://help.aliyun.com/zh/model-studio/).

## University Documents

The Korean university documents used in the local research corpus are third-party official materials and are not covered by the project code license. They are not redistributed in the public release boundary. Source, copyright, access, and non-endorsement information is recorded in the [Third-Party Data Notice](third_party_data_notice.md).

## Scope of This Notice

This file records the main dependencies used by the project; it is not a substitute for the complete license files supplied with each dependency. No trademark rights, institutional endorsement, or rights in third-party data, model weights, or hosted services are granted by the project license.
