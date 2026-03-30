# Fake CSAF Provider

> [!WARNING]
> In case the name of the project wasn't clear enough: Do not use this server in production. Its sole purpose is to serve in a test environment.

A small server application that can mimic several variants of CSAF providers, in order to test tools retrieving CSAF documents.

## Usage

> [!NOTE]
> Due to its history as a test util originally intended for only one person, the usage is currently very Debian-centric. If the demand for support on other operating systems arises, this can be remedied.

### Running on Host

To get started, run `scripts/setup.sh`. This generates a fake TLS certificate for the server, and then downloads and stores some CSAF-related tools, before downloading a lot of CSAF documents with label TLP:WHITE. From these, it generates (or rather fakes) some CSAF documents with other TLP labels.

> [!IMPORTANT]
> To successfully make requests to the server, you probably need to provide your client with the test root certificiate authority's TLS certificate. After running `scripts/setup.sh`, it is found in `crypto/ca.crt.pem`.

The heart of the project is the Flask server coded in `fake_csaf_provider/`. It can be started and stopped using `scripts/run.sh` and `scripts/stop.sh`. The scripts are merely there for convenience, the server can easily be run directly using a Python interpreter.

By default, the server runs on `localhost:34443`. You can specify the environment variables `FAKE_CSAF_DOMAIN` and `FAKE_CSAF_PORT` to adjust this behaviour. If you set the domain to anything other than "localhost", the server will bind to "0.0.0.0" instead of the loopback address.

### Running within Docker

This repository comes with a `Dockerfile` which creates a container with the necessary libraries installed to run the server. To build it, run:
``` sh
docker build -t fake_csaf_provider .
```
This creates an image called `fake_csaf_provider`.

Because the container is agnostic to how you incorporate it into your environment, it does *not* contain any TLS certificate or CSAF documents. Instead, these are intended to be mounted into the container. The server looks for its certificate in the container directory `/app/crypto`, and for the CSAF documents in `/app/csafs`. As a usage example, you can run the following command to achieve the same effect as running the server on the host system:
``` sh
docker run --rm -d --name fake_csaf_test -p 34443:34443 -v ./crypto:/app/crypto:ro -v ./csafs:/app/csafs:ro fake_csaf_provider
```

> [!IMPORTANT]
> The CSAF documents in the `csafs` folder need to follow the directory structure `csafs/<tlp>/<year>/id.json`. The script `collect_example_csaf_docs.sh` will create this structure for you.

If you use the container inside a Docker network, its domain will in general not be `localhost`. A different domain requires a different TLS certificate. You can create a fake one by calling:
``` sh
python3 -m fake_tls_certificate.main <some-domain> --days 30 --outdir ./crypto_other
```

This will create a fake certificate with a validity of 30 days and store it to `./crypto_other/<some-domain>.crt.pem`. The arguments are optional: The output directory defaults to `./crypto`, the number of days defaults to 365, and the domain defaults to `localhost`.

> [!IMPORTANT]
> The fake certificate is of course signed by a fake certificate authority. Its certificate is found in the output folder under `ca.crt.pem`. The client needs to accept this fake certificate as valid, otherwise it will refuse to connect to the server.

### OpenPGP Signatures

The server can provide OpenPGP signatures for CSAF documents, which is required by the CSAF standard for the CSAF Trusted Provider. When enabled, the server signs each CSAF document and makes the signatures available alongside the documents.

#### Generating OpenPGP Keys

The setup script automatically generates an OpenPGP key pair. To create a new key pair manually:

```sh
python3 -m fake_openpgp_key.main
```

This creates:
- `crypto/openpgp.key.asc` - Private key (ED25519, used for signing)
- `crypto/openpgp.pub.asc` - Public key (ED25519, distributed to clients)

> [!NOTE]
> If valid keys already exist, the script will reuse them instead of generating new ones. This ensures signature consistency across server restarts.

#### Enabling OpenPGP Signatures

To enable OpenPGP signatures, add the `--openpgp` flag when configuring the server:

```sh
scripts/configure.sh --well-known-meta --rolie-feed --openpgp
```

When enabled, the server provides:
- **Public key endpoint**: `/.well-known/openpgpkey.asc` - Clients can download the public key to verify signatures
- **Document signatures**: For each CSAF document (e.g., `advisory.json`), a detached signature file (e.g., `advisory.json.asc`) is automatically generated and served
- **Security.txt integration**: The public key URL is advertised in `security.txt` under the `Encryption:` field
- **ROLIE feed integration**: Signature links are included in ROLIE feed entries with `rel="signature"`

### Running servers in parallel

Testing to access several separate servers is most easily achieved via several docker containers. Since these will (inside the Docker network) be reachable under different domains, they require different TLS certificates to authenticate to the client. These can be generated via:
``` sh
python3 -m fake_tls_certificate.main <some-domain>
```
For example, using "mycsaf" as the domain name will create the files `./crypto/mycsaf.crt.pem`, `./crypto/mycsaf.key.pem` and `./crypto/mycsaf.chain.pem`.

> [!NOTE]
> Repeated calls to the script will only generate the certificate authority once, and reuse it in subsequent calls. This ensures that you only need to add a single CA to the client.

In order to tell the server which certificate to use, you can set the `FAKE_CSAF_DOMAIN` environment variable. If not set, its value will default to "localhost".

As an example, here is a minimal `docker-compose.yml` that starts a `fake_csaf_provider` service using the custom domain "mycsaf":

```yaml
networks:
  docker_network:
    driver: bridge
services:
    # This service name ensures that the "mycsaf" domain resolves to this container
    # inside the docker network.
    mycsaf:
        image: fake_csaf_provider
        container_name: fake_csaf_mycsaf
        environment:
            # This ensure that the correct TLS certificate is used,
            # and that the security.txt points to the correct domain.
            FAKE_CSAF_DOMAIN: "mycsaf"
            # Inside the container, the service should bind to the canonical
            # port for HTTPS communication.
            FAKE_CSAF_PORT: 443
        volumes:
            - ./crypto:/app/crypto:ro
            - ./csafs:/app/csafs:ro
        networks:
            - docker_network
```

Add other services to the same network ad libitum.

### Client Certificate Authentication

The server supports mutual TLS (mTLS) authentication using client certificates. This allows serving non-white TLP content (AMBER, GREEN, RED, etc.) to authenticated clients only.

#### Generating Client Certificates

The setup script automatically generates a test client certificate. To create additional client certificates:

```sh
python3 -m fake_tls_certificate.main --client-cert <client-name>
```

This creates:
- `crypto/<client-name>.crt.pem` - Client certificate
- `crypto/<client-name>.key.pem` - Client private key
- `crypto/<client-name>.chain.pem` - Combined certificate and key

All client certificates are signed by the same CA (`crypto/ca.crt.pem`) that signs the server certificate.

#### Using Client Certificates

To access protected TLP content, provide the client certificate and key when making requests:

```sh
curl --cacert crypto/ca.crt.pem \
     --cert crypto/testclient.crt.pem \
     --key crypto/testclient.key.pem \
     https://localhost:34443/some-amber-csaf-dir-for-rolie/2024/advisory.json
```

#### Testing Client Authentication

Run the test script to verify client certificate authentication is working:

```sh
./scripts/test_client_auth.sh
```

#### Provider Metadata

When ROLIE feeds are enabled, the provider metadata automatically advertises all available TLP levels. Clients with valid certificates can discover and access feeds for all TLP levels present in the `csafs/` directory.

### Configuration

The core design idea is that the server listens to PATCH requests on the path `/config`. The JSON payload should resemble the desired server configuration. The script `scripts/configure.sh` does exactly that. It can be provided with optional arguments to each feature flag that you want to enable.

By default, the server offers almost no endpoints. The most straightforward way to turn it into one flavour of CSAF provider is to call:
``` sh
scripts/configure.sh --well-known-meta --rolie-feed
```
The server then offers its metadata via the path `/.well-known/csaf/provider-metadata.json`, and serves the CSAF documents via a ROLIE feed that is specified in the metadata.

The endpoints can be verfieid by adding the `--verify` flag to the configure script:
``` sh
scripts/configure.sh --well-known-meta --rolie-feed --verify
```

More configuration options are described at the beginning of the script.
