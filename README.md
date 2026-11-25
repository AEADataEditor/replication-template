# replication-template

A template for starting a replication/ reproducibility exercise.

To start, DOWNLOAD or CLONE this repository
 - click on the green Download button over to the right
 - use [this link](https://github.com/AEADataEditor/replication-template/archive/master.zip)
 - from the command line,
```
wget https://github.com/AEADataEditor/replication-template/archive/master.zip
```

Afterwards, you should download the manuscript or article code archive, and unzip it on top of the template.

> Delete this README! (If you leave it, it's like keeping your price tag on your jacket...)

Finally, create a NEW repository, and commit the initial set of code (but not data). Then start running things!

We have a [document that has the most frequently used responses to authors](sample-language-report.md).

## Maintainer

- Lars Vilhuber, [@larsvilhuber](https://github.com/larsvilhuber)

## Where development happens (and where to report problems)

> [!IMPORTANT]
> This repository (`AEADataEditor/replication-template`) is a **published copy** that is overwritten on every release. Issues are disabled here and pull requests are not accepted.
>
> The upstream source is **[AEADataEditor/replication-template-development](https://github.com/AEADataEditor/replication-template-development)** (branch `development`). Report bugs in the scripts (`automations/`, `tools/`, `bitbucket-pipelines.yml`, `.claude/skills/`, ...) and submit fixes there, including bugs you find while working in an `aearep-NNNN` repository. Fixes made only in an `aearep-NNNN` repository are lost the next time `tools/update_tools.sh` runs.

## Contributions

If you would like to contribute, please [create a new issue](https://github.com/AEADataEditor/replication-template-development/issues/new/choose) or open a pull request in the [development repository](https://github.com/AEADataEditor/replication-template-development). Note that this template is used primarily for internal purposes for the AEA Data Editor, which may affect our ability to accept your contribution. 

## Contributors

The following have contributed to this repository:

<!-- CONTRIBUTORS:START -->
- aaf101, [@aaf101](https://github.com/aaf101)
- Anna Sundheim, [@ansu1338](https://github.com/ansu1338)
- Danny McGuire, [@dmcguir5](https://github.com/dmcguir5)
- David, [@dwasser](https://github.com/dwasser)
- Kacper Kowalik, [@Xarthisius](https://github.com/Xarthisius)
- Lars Vilhuber, [@larsvilhuber](https://github.com/larsvilhuber)
- LeonelBorjaPlaza, [@LeonelBorjaPlaza](https://github.com/LeonelBorjaPlaza)
- Meredith Welch, [@mswelch](https://github.com/mswelch)
- Michael Darisse, [@michaeldarisse](https://github.com/michaeldarisse)
- pdeffebach, [@pdeffebach](https://github.com/pdeffebach)
- Sofia Encarnacion, [@sencarn2](https://github.com/sencarn2)
- Takshil Sachdev, [@ts724](https://github.com/ts724)
<!-- CONTRIBUTORS:END -->

This list is updated automatically once a month by [update-contributors.yml](.github/workflows/update-contributors.yml).

## License

- **Code** (scripts and programs created in this repository, including `automations/`, `tools/`, `build/`, and `run.sh`): [BSD 3-Clause License](LICENSE). Each script carries a header with its SPDX license identifier, copyright years, and authors, maintained by `tools/license_headers.py`.
- **Documentation** (the `docs/` site, README files, report templates, and other Markdown/text documents): [CC BY-NC 4.0](LICENSE-docs.md).

  [![License: CC BY-NC 4.0](https://licensebuttons.net/l/by-nc/4.0/80x15.png)](https://creativecommons.org/licenses/by-nc/4.0/)

Both licenses cover only the files distributed with this template (see [NOTICE](NOTICE)). Files subsequently added to a repository created from this template, such as authors' replication materials or review reports, are not covered and remain subject to their own licenses and terms.

Third-party components keep their own licenses and are not covered by the above:

- `tools/inject_banner.py`: adapted from [SIVACOR/documentation](https://github.com/SIVACOR/documentation), CC BY 4.0.
- `PII_stata_scan.do`: adapted from [J-PAL/stata_PII_scan](https://github.com/J-PAL/stata_PII_scan), MIT License (Copyright (c) 2018 Marisa Carlos; full text in [licenses/](licenses/MIT-J-PAL-stata_PII_scan.txt)).
- `ado/`: the Stata package `filelist` by Robert Picard (SSC), under its author's terms.
