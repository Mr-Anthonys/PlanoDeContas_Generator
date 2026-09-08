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

Antes de gerar os scripts, o aplicativo pede login em um servidor SQL Server (ver [Conexão com o SQL Server](#conexão-com-o-sql-server)) — a geração dos scripts em si continua sendo local, prontos para conferir e executar manualmente (ou, dependendo da tela, executar direto na base do cliente logado).

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

## Histórico com um, dois ou três marcadores `@`

O texto do histórico (campo `Contas.Histórico`) pode conter um, dois ou três marcadores `@`. Esses marcadores **nunca são substituídos** pelo aplicativo — o texto gravado em `Contas.Histórico` mantém os `@` literais. O que o aplicativo grava, separadamente, em `InterfaceHistorico`, são os **nomes das colunas** do arquivo de origem que no futuro (em uma importação de dados, fora do escopo desta versão) substituirão cada marcador, na ordem em que aparecem. `Historico1`/`Historico2`/`Historico3` são campos de texto livre — o usuário escreve diretamente o nome da coluna:

* **Um marcador**: o usuário informa apenas `Historico1` (ex.: `Qtd`). `Historico2`/`Historico3` ficam vazios.
* **Dois marcadores**: o usuário informa `Historico1` (para o primeiro `@`) e `Historico2` (para o segundo `@`). `Historico3` fica vazio.
* **Três marcadores**: o usuário informa `Historico1`, `Historico2` e `Historico3` (um para cada `@`, na ordem em que aparecem).

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
| **5. InterfaceHistorico** | Grava, para cada conta, `Historico1`/`Historico2`/`Historico3` (colunas que substituirão os `@`) associados ao mesmo `ContaOrigem` da linha. |
| **6. InterfaceArq** | Parâmetros de leitura do arquivo para o `TipoArq` escolhido. |
| **7. InterfaceComum** | Mapeamento dos cabeçalhos do arquivo de origem para os campos lógicos do sistema. |
| **8. InterfaceFormaPgto** | Conversão da forma de pagamento do arquivo de origem para a forma usada pelo SGF. |

O usuário escolhe, por checkbox, quais dos 8 processos deseja gerar (um único processo, alguns deles, ou todos via **TODOS**). Ao clicar em **Gerar**, o aplicativo valida os dados e salva o(s) script(s) escolhido(s) em disco: um único arquivo `.sql` quando só um processo é selecionado, ou uma pasta com um arquivo por processo quando mais de um é selecionado.

Todo texto/valor gerado escapa apóstrofos (dobrando-os) e usa strings Unicode `N'...'`, preservando acentuação. Cada processo é independente (não depende de variáveis ou tabelas temporárias de outro script) e é embrulhado em uma transação `BEGIN TRY/BEGIN TRANSACTION ... COMMIT/CATCH ROLLBACK`, podendo ser executado isoladamente.

## Ordem recomendada de execução

```
1. GrupoPortal e GrupoContábil   (classificações-base)
2. Contas                        (usa os grupos acima)
3. InterfaceArq, InterfaceComum e InterfaceFormaPgto  (tipo/mapeamento de importação)
4. InterfaceContas                (vincula código de origem à conta)
5. InterfaceHistorico             (composição do histórico)
```

Essa é a ordem usada por `sql_generator.generate_full_script`, disponível para uso programático/testes mesmo sem uma aba dedicada na interface.

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

* O histórico (texto-base, `Historico1`/`Historico2`/`Historico3`) é único por lote de importação (aplicado a todas as contas importadas na mesma sessão), assim como no processo manual original — não há um histórico diferente por conta na mesma planilha.
* Suporta no máximo 3 marcadores `@` no histórico, pois a interface só oferece `Historico1`/`Historico2`/`Historico3` (os pares `Historico4`..`Historico8`/`Precedente4`..`8` existem na tabela real, porém nunca usados no processo atual e mantidos fixos como vazios nesta versão).
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

## Conexão com o SQL Server

Antes de abrir a janela principal, o aplicativo pede login em um servidor SQL Server. Há dois modos, com o automático preferido sempre que possível.

### Modo automático (variável de ambiente `GESTOR_PARAM`)

Replica o mesmo fluxo usado pelo Gestor Financeiro (VB6, `modBancoDeParametros.bas`): cada máquina tem uma variável de ambiente `GESTOR_PARAM` apontando para o servidor central de parâmetros.

1. O aplicativo lê `GESTOR_PARAM` do ambiente da máquina.
2. Conecta ao banco `Gestor_Parametros` desse servidor usando o login fixo do sistema (`Gestor_Parametros_Login` — o mesmo login usado pelo Gestor Financeiro, não é por usuário).
3. Lista os clientes cadastrados em `Gestor_Parametros.Parametros_Clientes` (nome, servidor, banco, usuário/senha daquele cliente, ODBC, diretórios, URLs de dashboard etc.).
4. O usuário escolhe o cliente na lista; o aplicativo conecta à base **daquele cliente** usando o Servidor/Usuário/Senha/Banco da linha selecionada, sem precisar digitar nada manualmente.

Se `GESTOR_PARAM` não estiver definida nesta máquina, ou a conexão ao banco central falhar (rede, permissão, driver ODBC ausente), o aplicativo cai automaticamente para o modo manual.

### Modo manual (fallback)

Servidor, usuário e senha digitados à mão, com um botão **Testar conexão** que lista as bases `Gestor_*` existentes no servidor informado para escolha da "base ativa". É o comportamento original da tela de login, preservado como alternativa — útil em máquinas sem `GESTOR_PARAM`, ou para acessar um servidor fora do registro central.

Um link no rodapé da tela de login alterna entre os dois modos a qualquer momento, sem precisar reiniciar o aplicativo.

### Onde isso mora no código

| Arquivo | Responsabilidade |
|---|---|
| `src/services/parametros_service.py` | Lê `GESTOR_PARAM`, conecta a `Gestor_Parametros`, lista/mapeia `Parametros_Clientes`. |
| `src/models/cliente_parametro.py` | Dataclass `ClienteParametro` — uma linha de `Parametros_Clientes`. |
| `src/services/db_connection_service.py` | Conexão genérica via `pyodbc` (usada tanto pelo login quanto pela Criação de Base). |
| `src/gui/connection_dialog.py` | Tela de login (modo automático + manual). |
| `src/models/session.py` | `SessionContext` — conexão viva + base ativa, repassado à janela principal. |

**Observação:** a aba "Criação de Base" **não** reaproveita as credenciais da sessão logada — tem seus próprios campos de "Servidor de produção" (pré-preenchidos com os dados da sessão atual como sugestão, mas editáveis). Isso é proposital: cada cliente em `Parametros_Clientes` pode estar hospedado em um servidor diferente, mas a base modelo escolhida precisa obrigatoriamente estar no **mesmo servidor** onde a base nova será criada (a cópia de dados em `03_dados.sql` referencia `[BaseModelo].dbo.Tabela` diretamente, sem linked server) — então "servidor onde eu logo para trabalhar" e "servidor onde eu provisiono uma base nova" são duas escolhas independentes, não a mesma coisa.

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

Fonte única de verdade para: opções de `TipoArq` (com seus dados de `InterfaceArq`/`InterfaceComum`/`InterfaceFormaPgto`), tipos de conta disponíveis, e as últimas configurações usadas pelo usuário (restauradas automaticamente na próxima abertura).

## Descrição da interface

Layout replica o protótipo Figma "Plano de Contas - Generator": três abas superiores clicáveis.

* **`Criar contas`** — a aba principal, descrita abaixo (importação de planilha, configurações gerais, barra de geração).
* **`Excluir contas`** — placeholder ("Em construção"); a lógica de exclusão ainda não foi especificada, nem no Python nem no CriaBase.
* **`Criação de base`** — provisiona a base de um cliente novo (schema, usuário SQL, cópia de dados de uma base modelo, cadastro do cartório e registro em `Parametros_Clientes`), reaproveitando a conexão de servidor da sessão logada — ver [Conexão com o SQL Server](#conexão-com-o-sql-server).

Dentro de `Criar contas`:

* **Importação da planilha**: botões `Selecionar planilha`, `Carregar`, `Limpar`, caminho do arquivo e tabela de pré-visualização (nome, código, grupo, situação — linhas inválidas destacadas).
* **Configurações gerais**: Regime (Interino/Titular, com a regra exibida), Tipo de Conta; `TipoArq`/`InterfaceComum`/`InterfaceFormaPgto` como campos de texto livre; quantidade de marcadores (um, dois ou três); texto do histórico; `Historico1`/`Historico2`/`Historico3` como campos de texto livre (desabilitados/limpos conforme a quantidade de marcadores escolhida).
* **Barra de geração**: botão `Validar Dados`, um checkbox por processo (`Contas`, `GrupoPortal`, `GrupoContábil`, `InterfaceContas`, `InterfaceHistorico`, `InterfaceArq`, `InterfaceComum`, `InterfaceFormaPgto`) mais `TODOS` para selecionar/desmarcar todos de uma vez, o botão `Gerar` (salva o(s) script(s) em disco) e o botão `Executar no banco` (roda os scripts selecionados direto na base ativa da sessão logada, via `session.connection`, com confirmação prévia — grava direto no banco do cliente e não é reversível automaticamente).
* Janela responsiva (abre maximizada, layout com pesos de grid) e redimensionável, com barra de status para mensagens de sucesso/erro. Erros de importação ou geração nunca fecham o aplicativo.

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
│   ├── gui/                   # connection_dialog, main_window, import_panel,
│   │                          #   configuration_panel, criar_base_panel
│   ├── models/                # Account, GenerationSettings, ClienteParametro, SessionContext
│   ├── services/              # excel_reader, validation_service, sql_generator,
│   │                          #   reference_loader, settings_service,
│   │                          #   db_connection_service, parametros_service, criar_base_service
│   └── utils/                 # sql_escape, constants
├── tests/                     # pytest (unitários + integração com Conchas)
├── docs/regras_identificadas.md
├── tools/gerar_modelo_importacao.py
└── examples/Modelo_Importacao_Atos.xlsx
```

## Melhorias futuras

A versão conectada ao SQL Server já existe (login automático/manual, execução direta dos scripts na base ativa via `Executar no banco`, e provisionamento de bases novas via `Criação de base` — ver [Conexão com o SQL Server](#conexão-com-o-sql-server)). Falta ainda:

* **Aba `Excluir contas`**: hoje é só um placeholder ("Em construção"); a lógica de exclusão ainda não foi especificada, nem no Python nem no CriaBase.
* Consultar o banco para validar se `ContaOrigem`, `Nome` ou `TipoArq` já existem antes de gerar o SQL (hoje a checagem é só dentro do próprio lote importado, mesmo com `Executar no banco` disponível).
* Pré-visualização do SQL antes de confirmar `Executar no banco` (hoje a confirmação é só um aviso textual, sem mostrar o script que será rodado).
* Suporte a mais de 3 marcadores `@` (a tabela `InterfaceHistorico` já tem `Historico4`..`Historico8` prontos no banco, apenas não utilizados pelo processo atual).
* Editor de `TipoArq`/`InterfaceComum`/`InterfaceFormaPgto` dentro da própria interface, em vez de editar `config.json` manualmente.
* Histórico de execuções (log de quais scripts já foram gerados/copiados/executados/provisionados).

## Licença

Distribuído sob a licença MIT — veja [`LICENSE`](LICENSE) para o texto completo.
