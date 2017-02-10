# coco.registry

This service creates a *registry* of other micro-services.


### Requirements

To run this service, you need to have :

* `conda` and `supervisord` installed. See [coco.main](https://github.com/factornado/coco.main)
* A mongo database that is up and running. If you don't have one, you can install one locally with:

    sudo apt-get install mongodb-server

### Installation

Clone the repository in the folder `coco.main/services`.

    cd coco.main/services
    git clone https://github.com/factornado/coco.registry

Build the service:

    ./coco.registry/services/myservice/make.sh

Edit the `config.yml` and tune the parameters.
You may eventually need to replace the registry port if `8800` is already used.
And you may need to tune the MongoDB address if you don't use a local install.

Restart supervisor:

    source activate supervisor
    supervisorctl reload
    supervisorctl start all

You should be able to test your service through the registry:

    curl http://localhost:8800/info

    > {"log.file": "/tmp/registry.log", "name": "registry", ...
