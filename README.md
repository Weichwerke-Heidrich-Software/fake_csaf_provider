# Fake CSAF Provider

> [!WARNING]
> In case the name of the project wasn't clear enough: Do not use this server in production. Its sole purpose is to serve in a test environment.

A small server application that can mimic several variants of CSAF providers, in order to test tools retrieving CSAF documents.

## Usage

> [!NOTE]
> Due to its history as a test util originally intended for only one person, the usage is currently very Debian-centric. If the demand for support on other operating systems arises, this can be remedied.

To get started, run `scripts/setup.sh`. This generates a fake TLS certificate for the server, and then downloads and stores some CSAF-related tools, before downloading a lot of CSAF documents with label TLP:WHITE. From these, it generates (or rather fakes) some CSAF documents with other TLP labels.

The heart of the project is the Flask server coded in `fake_csaf_provider/`. It can be started and stopped using `scripts/run.sh` and `scripts/stop.sh`. The scripts are merely there for convenience, the server can easily be run directly using a Python interpreter.

The core design idea is that the server listens to PATCH requests on the path `/config`. The JSON payload should resemble the desired server configuration. The script `scripts/configure.sh` does exactly that. It can be provided with optional arguments to each feature flag that you want to enable.

By default, the server offers almost no endpoints. The most straightforward way to turn it into one flavour of CSAF provider is to call:
```
scripts/configure.sh --well-known-meta --rolie-feed
```
The server then offers its metadata via the path `/.well-known/csaf/provider-metadata.json`, and serves the CSAF documents via a ROLIE feed that is specified in the metadata.

The endpoints can be verfieid by adding the `--verify` flag to the configure script:
```
scripts/configure.sh --well-known-meta --rolie-feed --verify
```

More configuration options are described at the beginning of the script.
