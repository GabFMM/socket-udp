# Socket UDP
## Como executar:
Todos os comandos devem ser executados na pasta raiz socket-udp
1. Configure a constante ENDPOINT_CHOSEN, para o cliente usar, em common/constants.py.
2. Gere os arquivos .txt, para a transferência entre a pasta cliente e a pasta servidor, com o seguinte comando:
```sh
python3 -m server.archive
```
3. execute o cliente com:
```sh
python3 -m client.main
```
4. execute o servidor com:
```sh
python3 -m server.main
```
