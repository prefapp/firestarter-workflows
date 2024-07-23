# Changelog

## [1.5.1](https://github.com/prefapp/firestarter-workflows/compare/v1.5.0...v1.5.1) (2024-07-23)


### Bug Fixes

* Fix error when registry field was missing ([#106](https://github.com/prefapp/firestarter-workflows/issues/106)) ([6baf1d9](https://github.com/prefapp/firestarter-workflows/commit/6baf1d9e71949b49364748802ca73c0ee3f38f27))

## [1.5.0](https://github.com/prefapp/firestarter-workflows/compare/v1.4.0...v1.5.0) (2024-07-23)


### Features

* Add registry config option ([#102](https://github.com/prefapp/firestarter-workflows/issues/102)) ([1de2511](https://github.com/prefapp/firestarter-workflows/commit/1de2511e60453144215b9aa85330f76cb9ec437e))
* add results to workflow run artifacts ([#91](https://github.com/prefapp/firestarter-workflows/issues/91)) ([42b910b](https://github.com/prefapp/firestarter-workflows/commit/42b910ba3665a9b15a3e9f149cde94e8b0768021))
* Fix versions with workflow call inputs ([#99](https://github.com/prefapp/firestarter-workflows/issues/99)) ([49afea0](https://github.com/prefapp/firestarter-workflows/commit/49afea0c51784e3a72e1ce9bfcfe7dd46a8349f5))

## [1.4.0](https://github.com/prefapp/firestarter-workflows/compare/v1.3.1...v1.4.0) (2024-07-05)


### Features

* Added base_paths env variable parsing ([#86](https://github.com/prefapp/firestarter-workflows/issues/86)) ([e46ebe5](https://github.com/prefapp/firestarter-workflows/commit/e46ebe5472c62cb6fa6ab1d5cf90b3fbbe73bfc1))


### Bug Fixes

* Build images workflow branch references ([#88](https://github.com/prefapp/firestarter-workflows/issues/88)) ([48b4c14](https://github.com/prefapp/firestarter-workflows/commit/48b4c144cd72474a4d0950c81973e47c34923e0b))

## [1.3.1](https://github.com/prefapp/firestarter-workflows/compare/v1.3.0...v1.3.1) (2024-07-03)


### Bug Fixes

* Delete typo ([#83](https://github.com/prefapp/firestarter-workflows/issues/83)) ([e224eb7](https://github.com/prefapp/firestarter-workflows/commit/e224eb7d5ce05a0d0fcb96e57f3c3aecc9b01dcd))

## [1.3.0](https://github.com/prefapp/firestarter-workflows/compare/v1.2.1...v1.3.0) (2024-07-03)


### Features

* Add dispatch matrix reusable workflow ([#67](https://github.com/prefapp/firestarter-workflows/issues/67)) ([a471998](https://github.com/prefapp/firestarter-workflows/commit/a4719981753cd6e46dbb70d321cd5507da8a3f6e))
* Add sops support in sys services ([#81](https://github.com/prefapp/firestarter-workflows/issues/81)) ([0613e5d](https://github.com/prefapp/firestarter-workflows/commit/0613e5ddb495d6ff5b67e764c02b9bd547133d0f))
* Add state repo reusable workflows ([#65](https://github.com/prefapp/firestarter-workflows/issues/65)) ([67b0f9a](https://github.com/prefapp/firestarter-workflows/commit/67b0f9a90596f38a53b8b68ba67f691c7cc26707))
* Added get_dispatch_matrix workflow ([#66](https://github.com/prefapp/firestarter-workflows/issues/66)) ([f194b0c](https://github.com/prefapp/firestarter-workflows/commit/f194b0cd5f9b9bdebb7170628fad7cefd6aafb65))
* Migrate hydrate step back to python ([#73](https://github.com/prefapp/firestarter-workflows/issues/73)) ([65fefe7](https://github.com/prefapp/firestarter-workflows/commit/65fefe7468c012b95629e59073e0ee65a9651e39))


### Bug Fixes

* Added default values ([#71](https://github.com/prefapp/firestarter-workflows/issues/71)) ([4e03cc7](https://github.com/prefapp/firestarter-workflows/commit/4e03cc7fe01e7c4f863a041e7e8c11fc0762ca42))
* Dispatch matrix workflow ([#68](https://github.com/prefapp/firestarter-workflows/issues/68)) ([ea81875](https://github.com/prefapp/firestarter-workflows/commit/ea8187557880386c0f6ab684a286ee5ace2d7ae9))
* Fix error when the app does not match exactly with the release ([#79](https://github.com/prefapp/firestarter-workflows/issues/79)) ([8e30f70](https://github.com/prefapp/firestarter-workflows/commit/8e30f70a3b7b1c9a098f35186d73bbe77b5ebc18))
* Fixed extra_registries in execute function ([#82](https://github.com/prefapp/firestarter-workflows/issues/82)) ([3370d7a](https://github.com/prefapp/firestarter-workflows/commit/3370d7a12f4765cadab7b88013813e33fd8cea7f))
* Removed uses of property already_logged_in_providers ([#63](https://github.com/prefapp/firestarter-workflows/issues/63)) ([dff1259](https://github.com/prefapp/firestarter-workflows/commit/dff1259d72f28c6375a0a2f2a8c21d28682b751d))
* Specify kind of events to handle in dorny paths ([#75](https://github.com/prefapp/firestarter-workflows/issues/75)) ([0ccd9b3](https://github.com/prefapp/firestarter-workflows/commit/0ccd9b3abb26991308d7158b04986f4a825a3d70))
* Support empty diffs ([#78](https://github.com/prefapp/firestarter-workflows/issues/78)) ([8b490f4](https://github.com/prefapp/firestarter-workflows/commit/8b490f4c937f7faface83201fe4507d3dd222cf8))

## [1.2.1](https://github.com/prefapp/firestarter-workflows/compare/v1.2.0...v1.2.1) (2024-05-08)


### Bug Fixes

* major tag format ([c60031e](https://github.com/prefapp/firestarter-workflows/commit/c60031e1f2e46f56c4cf7ee888efa530ffc00ca7))

## [1.2.0](https://github.com/prefapp/firestarter-workflows/compare/v1.1.1...v1.2.0) (2024-05-08)


### Features

* trigger movement of major tag only on release ([976ed31](https://github.com/prefapp/firestarter-workflows/commit/976ed313c565000630af80ee816d5666da1b7942))


### Bug Fixes

* dagger workflow ref ([#59](https://github.com/prefapp/firestarter-workflows/issues/59)) ([4e6fde3](https://github.com/prefapp/firestarter-workflows/commit/4e6fde34c6badc003eb8e88603a951c40c0eabd6))

## [1.1.1](https://github.com/prefapp/firestarter-workflows/compare/v1.1.0...v1.1.1) (2024-05-07)


### Bug Fixes

* release-please workflow ([af9431b](https://github.com/prefapp/firestarter-workflows/commit/af9431b01c7c3b25b3b8d4dc6d3fd2f2eb0b50ad))
* release-please workflow ([b9012df](https://github.com/prefapp/firestarter-workflows/commit/b9012df32cc26e82dfb8b5499dab6975d41d8482))
* release-please workflow ([1b5f7a7](https://github.com/prefapp/firestarter-workflows/commit/1b5f7a7a86aea9652d45a0bfc49ee033202b7b07))
* release-please workflow ([9d6e4a5](https://github.com/prefapp/firestarter-workflows/commit/9d6e4a50fee36ea34945f57537b7717847e21cbf))

## [1.1.0](https://github.com/prefapp/firestarter-workflows/compare/v1.0.1...v1.1.0) (2024-05-07)


### Features

* Add support for generic auth ([8cdff08](https://github.com/prefapp/firestarter-workflows/commit/8cdff086b39dea58e418cc0636ce3d702ae451a5))

## [1.0.1](https://github.com/prefapp/firestarter-workflows/compare/v1.0.0...v1.0.1) (2024-04-24)


### Bug Fixes

* Fixed normalize_image_tag function so it also accepts the _ character ([#53](https://github.com/prefapp/firestarter-workflows/issues/53)) ([78a56e1](https://github.com/prefapp/firestarter-workflows/commit/78a56e19c8758ba2d775976a0406f4ba9fa86b8d))

## [1.0.0](https://github.com/prefapp/firestarter-workflows/compare/v0.1.0...v1.0.0) (2024-04-16)


### ⚠ BREAKING CHANGES

* release v1 ([#51](https://github.com/prefapp/firestarter-workflows/issues/51))

### Features

* release v1 ([#51](https://github.com/prefapp/firestarter-workflows/issues/51)) ([ca08c5b](https://github.com/prefapp/firestarter-workflows/commit/ca08c5bd28545e730924ac04e7b62158456e6bda))

## 0.1.0 (2024-04-16)


### Features

* [build_images] Add secrets support from within dockerfile ([#28](https://github.com/prefapp/firestarter-workflows/issues/28)) ([071b80e](https://github.com/prefapp/firestarter-workflows/commit/071b80e0d436ce786769775b4d62e174b91cb965))
* Add config secret rendering ([#46](https://github.com/prefapp/firestarter-workflows/issues/46)) ([0673c73](https://github.com/prefapp/firestarter-workflows/commit/0673c73039fb9c628a8b9d488e9974b76e6228d5))
* Add CONTRIBUTING guide ([#11](https://github.com/prefapp/firestarter-workflows/issues/11)) ([b436fd4](https://github.com/prefapp/firestarter-workflows/commit/b436fd4e0895c90475bae804fea597ae642af51c))
* add firestarter namespace ([aaea725](https://github.com/prefapp/firestarter-workflows/commit/aaea72574baec0be701f9bbbdb230abb7f1af95e))
* Add login strategy for azure ([#31](https://github.com/prefapp/firestarter-workflows/issues/31)) ([d88483c](https://github.com/prefapp/firestarter-workflows/commit/d88483c0cf0e8b576f094d8a469c31d0152b7515))
* add main method ([2876b44](https://github.com/prefapp/firestarter-workflows/commit/2876b44651226707704d1e24ba867748a1d56c88))
* add new on_premises workflow ([4a18869](https://github.com/prefapp/firestarter-workflows/commit/4a18869efe8f405c05ff8dcea940d684cf42bcea))
* Added support for multiple registries via the extra_registries config value ([#44](https://github.com/prefapp/firestarter-workflows/issues/44)) ([c0a11cb](https://github.com/prefapp/firestarter-workflows/commit/c0a11cb5837cf5652c57bfa57b0eae1c374650c1))
* Allow receiving input from env vars [#7](https://github.com/prefapp/firestarter-workflows/issues/7) from prefapp/feature/6-input-env-vars ([2346d4e](https://github.com/prefapp/firestarter-workflows/commit/2346d4ec6401c44f2149c97d964924e6108adab2))
* build images workflow v1 ([#47](https://github.com/prefapp/firestarter-workflows/issues/47)) ([0b94fcd](https://github.com/prefapp/firestarter-workflows/commit/0b94fcdfceddb08518d17b86df702afe43f8106d))
* provision CODEOWNERS file ([8263359](https://github.com/prefapp/firestarter-workflows/commit/82633594407029e11766aaea773709bd2d71889d))
* provision CODEOWNERS file ([00e21f8](https://github.com/prefapp/firestarter-workflows/commit/00e21f8f2edbbb9f3d51577626a43d36c0f7088a))
* provision CODEOWNERS file ([bd090e9](https://github.com/prefapp/firestarter-workflows/commit/bd090e9122994820a35a0acbe3acaed61368570a))
* release please ([#48](https://github.com/prefapp/firestarter-workflows/issues/48)) ([f745156](https://github.com/prefapp/firestarter-workflows/commit/f7451560374f352b371329a75e82d3164e53dd0b))
* set default to all flavors (*) ([3a10bf7](https://github.com/prefapp/firestarter-workflows/commit/3a10bf740b4973225a1f46ebad25fc3d3ce5f071))
* test on_premises ([dff4b57](https://github.com/prefapp/firestarter-workflows/commit/dff4b57b1bb1d384801fd9ac187af31da19b4110))
* test pr_verify ([10055cd](https://github.com/prefapp/firestarter-workflows/commit/10055cde68968c04d9c76e7eef39d2aff1616270))
* test pr_verify ([02eec3d](https://github.com/prefapp/firestarter-workflows/commit/02eec3d2b796540a9020fdea785f385a9b6d55bb))
* Upgrade dagger to 0.8.0 ([#38](https://github.com/prefapp/firestarter-workflows/issues/38)) ([7106ce5](https://github.com/prefapp/firestarter-workflows/commit/7106ce5bddae66682fb17ab516767f0af9b0641b))


### Bug Fixes

* add init ([a4af075](https://github.com/prefapp/firestarter-workflows/commit/a4af0756b63cf5b31cfd3254a1bc18b1485ee8db))
* Check status code in acr login [#5](https://github.com/prefapp/firestarter-workflows/issues/5) from prefapp/fix/azure-login-error ([6e78c67](https://github.com/prefapp/firestarter-workflows/commit/6e78c67347a78e73b19a2e1b9bcd6ae00394a23d))
* Delete import from old dependency ([#36](https://github.com/prefapp/firestarter-workflows/issues/36)) ([56dc951](https://github.com/prefapp/firestarter-workflows/commit/56dc951d616b79d7def55eba7e62411b91fdbaf4))
* Fix build images dependencies ([#33](https://github.com/prefapp/firestarter-workflows/issues/33)) ([c7a7e09](https://github.com/prefapp/firestarter-workflows/commit/c7a7e091de33b51f6abad0b0f203f51bc948f035))
* keys accesss using * for building flavors ([4912e30](https://github.com/prefapp/firestarter-workflows/commit/4912e30454b8f8b5b8712a7e8ee57792aa4ca28d))
* object access ([c2d0738](https://github.com/prefapp/firestarter-workflows/commit/c2d07386f34736a4d003d31030f18554fd3bbfef))
* object access ([764d21d](https://github.com/prefapp/firestarter-workflows/commit/764d21d412b1d5a428d115ddfec93b84332597ec))
* packages ([79493e3](https://github.com/prefapp/firestarter-workflows/commit/79493e390b9866eedc4df4a0a02cd5db92f974c3))
* poetry.lock ([aee587b](https://github.com/prefapp/firestarter-workflows/commit/aee587bd1b70c7e18f4244c648e55ae87d5ad9d6))
* remove unused modules ([9e47a92](https://github.com/prefapp/firestarter-workflows/commit/9e47a922d9f0a6bf3dad0aec66ee97e20ac8e060))
* rename base method ([b645824](https://github.com/prefapp/firestarter-workflows/commit/b645824a3cac9f6abb93fe94601ee245fe8a231f))
* require only python 3.10 ([52a7472](https://github.com/prefapp/firestarter-workflows/commit/52a7472ac6ddf6c668ff1a4d0ffce16292da2d9c))
* secrets ([#49](https://github.com/prefapp/firestarter-workflows/issues/49)) ([5791772](https://github.com/prefapp/firestarter-workflows/commit/57917721de88d0b70711fe58b9e32bf7a0c1255b))


### Documentation

* Update README.md ([d6bcd2e](https://github.com/prefapp/firestarter-workflows/commit/d6bcd2e33471e17a9d6212c098e8e1bc332c0d86))
