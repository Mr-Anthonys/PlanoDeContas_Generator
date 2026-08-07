# Gerador de Plano de Contas e Scripts SQL

Aplicativo desktop para Windows (Python + Tkinter) que substitui o processo manual, feito em planilhas Excel, de geração dos scripts SQL Server para cadastro de contas e das tabelas de interface de importação. O aplicativo lê uma planilha simples (`Nome`, `Grupo`, `ContaOrigem`), aplica as configurações informadas pelo usuário e gera, prontos para conferir, copiar (`Ctrl+C`) e colar no SQL Server, os scripts de:

1. `Contas`
2. `GrupoPortal`
3. `GrupoContábil`
4. `InterfaceContas`
5. `InterfaceHistorico`
6. `InterfaceArq`
7. `InterfaceComum`
8. `InterfaceFormaPgto`

Nesta primeira versão o aplicativo **não se conecta ao banco de dados** — a execução dos scripts continua sendo manual, no SQL Server Management Studio ou ferramenta equivalente.

## Arquivos de referência analisados

* `Documentacao_Plano_de_Contas_Receitas_Atualizada.docx` — documentação funcional/técnica do processo atual (fonte principal das regras de negócio).
* `PLANO DE CONTAS - RECEITAS.xlsx` — planilha modelo (em branco), usada para confirmar nomes exatos de tabelas/colunas e fórmulas.
* `Plano de Contas Receitas - Conchas.xlsx` — planilha real preenchida (31 contas), usada como exemplo de integração e para confirmar valores reais.

Nenhum desses arquivos foi modificado. O levantamento completo das regras, com citação de célula/linha de origem, está em [`docs/regras_identificadas.md`](docs/regras_identificadas.md).

## Formato da planilha de entrada

A planilha `.xlsx` de importação deve conter apenas três colunas:

| Nome                    | Grupo                | ContaOrigem |
| ----------------------- | --------------------- | ----------: |
| RECONHECIMENTO DE FIRMA | TABELIONATO DE NOTAS  |           1 |
| AUTENTICAÇÃO            | TABELIONATO DE NOTAS  |           2 |
| PROTESTO DE TÍTULO      | PROTESTO              |           3 |

* **Nome**: nome da conta/ato. Aceita cabeçalhos alternativos: `Nome`, `Nome da Conta`, `Conta`, `Nome do Ato`.
* **Grupo**: grupo contábil da conta. Aceita: `Grupo`, `Grupo Contábil`, `GrupoContábil`, `NomeGrupo`.
* **ContaOrigem**: código da conta, usado exatamente como informado (nunca gerado, consultado ou inferido pelo aplicativo). Aceita: `ContaOrigem`, `Conta Origem`, `Código`, `Codigo`, `Código da Conta`, `Codigo da Conta`, `CodConta`.

Um modelo pronto está em [`examples/Modelo_Importacao_Atos.xlsx`](examples/Modelo_Importacao_Atos.xlsx), com uma aba de instruções.

Linhas totalmente vazias são ignoradas. Espaços no início/fim são removidos automaticamente. Zeros à esquerda em `ContaOrigem` são preservados quando a célula estiver formatada como texto. Planilhas sem alguma das três colunas, sem contas válidas, corrompidas ou abertas em outro programa geram uma mensagem de erro clara, sem travar o aplicativo.

## Regime: Interino e Titular

Antes de gerar os scripts, o usuário escolhe o regime da conta:

```
Interino = L_IRRF 0
Titular  = L_IRRF 1
```

Essa regra é exibida diretamente na interface, ao lado da escolha.

## Histórico com um e dois marcadores `@`

O texto do histórico (campo `Contas.Histórico`) pode conter um ou dois marcadores `@`. Esses marcadores **nunca são substituídos** pelo aplicativo — o texto gravado em `Contas.Histórico` mantém os `@` literais. O que o aplicativo grava, separadamente, em `InterfaceHistorico`, são os **nomes das colunas** do arquivo de origem que no futuro (em uma importação de dados, fora do escopo desta versão) substituirão cada marcador, na ordem em que aparecem:

* **Um marcador**: o usuário informa apenas `Historico1` (ex.: `Qtd`). `Historico2` fica vazio.
* **Dois marcadores**: o usuário informa `Historico1` (para o primeiro `@`) e `Historico2` (para o segundo `@`).

Exemplo:

```
Contas.Histórico = EMOLUMENTOS RECEBIDOS - QTD DE ATOS @ PROTOCOLO: @
Historico1 = Qtd
Historico2 = Protocolo
```

O aplicativo valida que a quantidade de `@` no texto bate exatamente com a quantidade de marcadores escolhida, bloqueando a geração dos scripts enquanto houver divergência.

## Processos SQL gerados

| Painel | O que faz |
|---|---|
| **1. Contas** | Um `INSERT` por conta importada, com proteção `IF NOT EXISTS` pelo Nome. |
| **2. GrupoPortal** | Um registro por grupo **realmente usado** pelas contas importadas (não repete grupos). |
| **3. GrupoContábil** | Idem, para a tabela `GrupoContábil`. |
| **4. InterfaceContas** | Vincula `ContaOrigem` (exatamente como informado na planilha) ao nome da conta (`ContaSGF`) e ao `TipoArq` escolhido. |
| **5. InterfaceHistorico** | Grava, para cada conta, `Historico1`/`Historico2` (colunas que substituirão os `@`) associados ao mesmo `ContaOrigem` da linha. |
| **6. InterfaceArq** | Parâmetros de leitura do arquivo para o `TipoArq` escolhido. |
| **7. InterfaceComum** | Mapeamento dos cabeçalhos do arquivo de origem para os campos lógicos do sistema. |
| **8. InterfaceFormaPgto** | Conversão da forma de pagamento do arquivo de origem para a forma usada pelo SGF. |
| **9. Script completo** | Reúne os 8 processos acima, na ordem lógica de execução, com comentários separadores. |

Cada painel tem título, descrição, área de texto SQL somente leitura (fonte monoespaçada), contador de comandos gerados e botão **Copiar** (copia somente aquele processo). Há também os botões **Copiar todos os scripts** e **Salvar SQL em arquivo** / **Salvar cada processo separadamente**.

Todo texto/valor gerado escapa apóstrofos (dobrando-os) e usa strings Unicode `N'...'`, preservando acentuação. Cada processo é independente (não depende de variáveis ou tabelas temporárias de outro script) e é embrulhado em uma transação `BEGIN TRY/BEGIN TRANSACTION ... COMMIT/CATCH ROLLBACK`, podendo ser executado isoladamente.

## Ordem recomendada de execução

```
1. GrupoPortal e GrupoContábil   (classificações-base)
2. Contas                        (usa os grupos acima)
3. InterfaceArq, InterfaceComum e InterfaceFormaPgto  (tipo/mapeamento de importação)
4. InterfaceContas                (vincula código de origem à conta)
5. InterfaceHistorico             (composição do histórico)
```

Essa é a ordem usada na aba "Script completo".

## Correções realizadas em relação à planilha original

Confirmadas por análise célula a célula das fórmulas (ver `docs/regras_identificadas.md` para o detalhamento com citação de célula):

1. **Apóstrofo indevido em `GrupoPortal`.** A fórmula original (`=CONCATENATE(C75,"')")`) gerava `VALUES('NOME',0')` — SQL inválido. Corrigido para `VALUES('NOME',0)`.
2. **Grupos inconsistentes.** No Conchas, 16 das 31 contas usam o grupo `PROTESTO`, que nunca era cadastrado em `GrupoPortal`/`GrupoContábil` (por erro humano de reaproveitamento, o grupo `REGISTRO CIVIL` era criado no lugar, sem nunca ser usado). O aplicativo deriva os grupos automaticamente a partir dos grupos realmente usados pelas contas importadas, eliminando essa classe de erro por construção.
3. **Ausência de proteção contra duplicidade.** No processo manual, apenas `Contas` tinha `IF NOT EXISTS`. Todos os 8 processos gerados pelo aplicativo agora têm essa proteção.
4. **`ContaOrigem` tratado como texto.** As fórmulas de `InterfaceContas`/`InterfaceHistorico` sempre geravam o código entre aspas simples, mesmo sendo um valor numérico na célula. O aplicativo reproduz esse comportamento (string, preservando zeros à esquerda), em vez de tratá-lo como número.
5. **`Historico1 = "Historico"` no Conchas não é um padrão válido.** Nos dados reais do Conchas, todas as 31 linhas de `InterfaceHistorico` gravam `Historico1` como a string literal `"Historico"`, que não corresponde a nenhuma coluna configurada em `InterfaceComum` (que tem `Qtd`, `Protocolo` etc.). Interpretamos isso como um **erro de preenchimento no arquivo original** (provável cópia/colagem incorreta), e não como uma regra a reproduzir. O aplicativo oferece como opções os nomes que de fato existem em `InterfaceComum` para os TipoArq cadastrados: `Qtd`, `Protocolo`, `LivroFolha`.
6. **Falta de transação/rollback.** Nenhum processo do arquivo original usava transação. Todos os scripts gerados agora são embrulhados em `BEGIN TRY/TRANSACTION ... COMMIT/CATCH ROLLBACK`.
7. **Capacidade fixa de linhas.** O arquivo original tinha áreas de entrada fixas (31 contas, 2 grupos etc.). O aplicativo não tem esse limite — qualquer quantidade de contas/grupos pode ser importada.
8. **Inconsistência de espaço em "N/A".** Identificamos que `InterfaceComum.LocalForma` grava `" N/A"` (com espaço) enquanto `InterfaceFormaPgto.FormaSist` grava `"N/A"` (sem espaço) — mantido fielmente conforme a planilha de referência, pois não há evidência de qual é o valor correto sem confirmação externa junto ao sistema de origem; reproduzimos o valor real observado em cada tabela.

## Limitações da primeira versão

* Não há conexão direta com o banco de dados — a execução dos scripts é manual.
* O histórico (texto-base, `Historico1`/`Historico2`) é único por lote de importação (aplicado a todas as contas importadas na mesma sessão), assim como no processo manual original — não há um histórico diferente por conta na mesma planilha.
* Suporta no máximo 2 marcadores `@` no histórico, pois a tabela `InterfaceHistorico` só tem `Historico1`/`Historico2` (mais 6 pares `Historico3`..`Historico8`/`Precedente3`..`8` existentes na tabela real, porém nunca usados no processo atual e mantidos fixos como vazios nesta versão).
* Os 3 conjuntos de `TipoArq`/`InterfaceComum`/`InterfaceFormaPgto` disponíveis (`Emolumentos`, `Emolumentos_Protesto`, `Emolumentos_Notas`) são os confirmados na planilha de referência; novos tipos exigem editar `config.json`.
* Sem suporte a múltiplos idiomas ou temas.

## Como instalar

Pré-requisitos: Python 3.12+ no Windows.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como executar

```bat
.venv\Scripts\activate
python app.py
```

## Como executar os testes

```bat
.venv\Scripts\activate
python -m pytest -q
```

A suíte inclui testes unitários de leitura de planilha, validação, regras de histórico e geração de SQL, além de um **teste de integração com o arquivo real `Plano de Contas Receitas - Conchas.xlsx`** (`tests/test_conchas_integration.py`), que extrai as 31 contas originais diretamente da planilha, monta uma planilha de importação equivalente e confirma que a quantidade de contas, os códigos (sem inversão/reordenação) e os grupos gerados (corrigidos) batem com o esperado.

## Como gerar o executável

```bat
build.bat
```

O script `build.bat`: cria/reaproveita um ambiente virtual, instala as dependências, executa a suíte de testes (o build é interrompido se algum teste falhar) e gera o executável com PyInstaller, sem janela de terminal (`--windowed`).

**Executável gerado:** `dist\GeradorPlanoContas.exe` (o `build.bat` também copia `config.json` para dentro de `dist\`, pois o executável lê/grava esse arquivo ao lado do `.exe` — necessário para persistir as últimas configurações usadas e para permitir customizar os valores de referência sem recompilar).

## Arquivo de configuração (`config.json`)

Fonte única de verdade para: opções de `TipoArq` (com seus dados de `InterfaceArq`/`InterfaceComum`/`InterfaceFormaPgto`), opções de `Historico1`/`Historico2`, tipos de conta disponíveis, e as últimas configurações usadas pelo usuário (restauradas automaticamente na próxima abertura; há um botão **Restaurar padrões** na interface).

## Descrição da interface

* **Importação da planilha**: botões `Selecionar planilha`, `Carregar`, `Limpar`, caminho do arquivo e tabela de pré-visualização (linha, nome, grupo, ContaOrigem, situação — linhas inválidas destacadas).
* **Configurações gerais**: Regime (Interino/Titular, com a regra exibida), Tipo de Conta, TipoArq, InterfaceComum, InterfaceFormaPgto, quantidade de marcadores, texto do histórico, Historico1/Historico2 (Historico2 desabilitado quando há apenas 1 marcador).
* **Ações**: `Validar dados`, `Gerar scripts`, `Copiar todos os scripts`, `Salvar SQL em arquivo`, `Salvar cada processo separadamente`, `Restaurar padrões`.
* **Scripts**: 9 abas (8 processos + Script completo), cada uma com texto SQL somente leitura, contador de comandos e botão `Copiar`.
* Janela centralizada, redimensionável, com barra de status para mensagens de sucesso/erro. Erros de importação ou geração nunca fecham o aplicativo.

## Estrutura do projeto

```
plano-contas-generator/
├── app.py                     # ponto de entrada
├── config.json                # fonte única de verdade (referência + últimas configurações)
├── build.bat                  # cria venv, instala deps, testa e empacota o .exe
├── requirements.txt
├── pytest.ini
├── conftest.py
├── src/
│   ├── gui/                   # main_window, import_panel, configuration_panel, sql_tabs
│   ├── models/                # Account, GenerationSettings
│   ├── services/              # excel_reader, validation_service, sql_generator,
│   │                          #   reference_loader, settings_service
│   └── utils/                 # sql_escape, constants
├── tests/                     # pytest (unitários + integração com Conchas)
├── docs/regras_identificadas.md
├── tools/gerar_modelo_importacao.py
└── examples/Modelo_Importacao_Atos.xlsx
```

## Sugestões para uma futura versão conectada ao SQL Server

* Executar os scripts diretamente via `pyodbc`/`pymssql`, com pré-visualização e confirmação antes do commit.
* Consultar o banco para validar se `ContaOrigem`, `Nome` ou `TipoArq` já existem antes de gerar o SQL (hoje a checagem é só dentro do próprio lote importado).
* Suporte a mais de 2 marcadores `@` (a tabela `InterfaceHistorico` já tem `Historico3`..`Historico8` prontos no banco, apenas não utilizados pelo processo atual).
* Editor de `TipoArq`/`InterfaceComum`/`InterfaceFormaPgto` dentro da própria interface, em vez de editar `config.json` manualmente.
* Histórico de execuções (log de quais scripts já foram gerados/copiados/executados).

## Licença

Distribuído sob a licença MIT — veja [`LICENSE`](LICENSE) para o texto completo.
