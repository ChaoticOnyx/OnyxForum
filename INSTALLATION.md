# Установка

Для установки вам потребуется:

- [Docker Desktop](https://www.docker.com/get-started/)

Затем необходимо собрать Docker образ (это нужно сделать только один раз):

```sh
$ ./docker/build_dev.sh
```

Теперь можно запускать:

```sh
$ ./docker/run_dev.sh
```

Готово! У вас запущен форум на `127.0.0.1:5000`.

Для разработки запущенного форума можно использовать VSCode - для этого потребуется установить расширение [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
