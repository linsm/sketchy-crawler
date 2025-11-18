# SketchyCrawler

This repository hosts SketchyCrawler, the prototype introduced in our paper [Unveiling the Critical Attack Path for Implanting Backdoors in Supply Chains: Practical Experience from XZ](https://doi.org/10.1007/978-981-95-4434-9_24). It includes the crawler, analysis components, and various tooling used to detect sketchy or malicious indicators in open-source projects.

## How to run it?

To configure your environment, start by copying the `.env.template` file to `.env`:
```
cp .env.template .env
```
Then modify the values in `.env` accordingly:

### 
If you want to include build dependencies of apt packages, please ensure that you have activated the deb-src packages in your sources.list file. 

### GitHub Configuration
- `GITHUB_TOKEN`: GitHub Personal Access Token (supports higher rate limit)

### First run

If this is your first run, you haven't fetched any commits yet, so you'll need to perform a full run:

```shell
python3 sketchycrawler.py fullrun --targets=crawling-targets.csv
```

The command above will store the commits in the 'results' directory, so you won't need to use the GitHub API again to fetch them, thus avoiding rate limiting.
Afterwards, the crawler will automatically detect that the commits for a specific repository are already fetched and will skip them. 
If you want to fetch them again from scratch it is sufficient to delete the corresponding commit file located in the results directory.

### Evaluation

We used packages from [Debian Popcon](https://popcon.debian.org/main/by_inst), which have source code hosted on GitHub. 
Additionally, we also wanted to verify a package written in Rust so we crawled the list to find the first Rust package with the most installations. 

To find packages developed in Rust, you can just copy the content provided on [Debian Popcon](https://popcon.debian.org/main/by_inst)
into the file 'evaluation/debian-popcon'. Afterwards you can run the following script:

```shell
cd evaluation
./find-rust-packages.sh
```

## Acknowledgment

This work has been carried out within the scope of Digidow, the Christian Doppler Laboratory for Private Digital Authentication in the Physical World and has partially been supported by the LIT Secure and Correct Systems Lab. 
We gratefully acknowledge financial support by the Austrian Federal Ministry of Labour and Economy, the National Foundation for Research, Technology and Development, the Christian Doppler Research Association, 3 Banken IT GmbH, ekey biometric systems GmbH, Kepler Universitätsklinikum GmbH, NXP Semiconductors Austria GmbH & Co KG, Österreichische Staatsdruckerei GmbH, and the State of Upper Austria.

## LICENSE

Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

**License**: [European Union Public License v1.2](https://joinup.ec.europa.eu/software/page/eupl)

