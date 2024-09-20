# dcgm-snap

This is a snap delivering NVIDIA dcgm components.
The snap consists of [dcgm](https://developer.nvidia.com/dcgm) and [dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter).

## Build the snap

You can build the snap locally by using the command:

```shell
snapcraft --use-lxd
```

## Test

You can test the snap locally by using the command:

```shell
tox -e func
```

User documentation can be found on the [snap page](https://snapcraft.io/dcgm).
