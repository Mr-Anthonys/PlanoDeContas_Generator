# Status: Conexão SQL Server + "Criação de Base" (Fase 1 concluída)

Registro de onde paramos, pra continuar depois sem precisar reconstruir o
contexto do zero. Veja também `docs/regras_identificadas.md` (regras de
negócio do gerador de contas) — este arquivo é só sobre a feature nova.

## Objetivo original

Trazer a lógica do app C# separado **CriaBase**
(`../CriaBase/CriaBase`, fora deste repositório) pra dentro do Plano de
Contas - Generator, na aba "Criação de base", de um jeito mais guiado:
login obrigatório no SQL Server ao abrir o app, as 3 abas (Criar Contas /
Excluir Contas / Criação de Base) só liberadas depois de conectar, e
"Criar Contas"/"Excluir Contas" passando a poder executar direto no banco
(antes só geravam `.sql` pra copiar).

## O que já está implementado e testado

- **Login obrigatório** (`src/gui/connection_dialog.py`): servidor/usuário/
  senha, testa conexão, lista bases `Gestor_*` (`sys.databases`), exige
  escolher a "base ativa" antes de liberar o "Conectar". `app.py` só abre a
  `MainWindow` depois disso.
- **3 abas reais com troca de fato** (`src/gui/main_window.py`): antes eram
  só rótulos estáticos decorativos do Figma. Agora são clicáveis
  (`_switch_tab`, padrão `tkraise` sobre frames empilhados no mesmo grid).
  - **Criar Contas**: conteúdo original preservado (import + configuração +
    barra de botões), só ganhou um botão novo "Executar no banco" que roda
    o SQL gerado direto na base ativa (com confirmação antes).
  - **Excluir Contas**: só um placeholder ("Em construção") — **sem lógica
    nenhuma implementada ainda**, ver "Pendências" abaixo.
  - **Criação de Base**: painel novo completo (`src/gui/criar_base_panel.py`).
- **Orquestração da criação de base** (`src/services/criar_base_service.py`
  + `src/services/sql_batch_executor.py` + `src/services/db_connection_service.py`):
  reaproveita os 7 `.sql` originais do CriaBase, copiados pra
  `resources/sql_templates/criar_base/` (`01_schema.sql` ... `07_interino.sql`).
  Roda em thread separada (`threading` + `queue.Queue` + `MainWindow.after`)
  pra não travar a interface durante o schema (274 lotes `GO`).
- **Testes**: `tests/test_sql_batch_executor.py` e
  `tests/test_criar_base_service.py` (18 testes novos, com
  `FakeCursor`/`FakeConnection` em `tests/conftest.py`) — cobrem split de
  lotes `GO`, substituição de placeholders, e "parar no primeiro erro".
  Suíte completa: **74/74 passando** (`pytest -q`).
- Validado visualmente (screenshots reais do app rodando) o diálogo de
  login e as 3 abas com uma sessão simulada (`FakeConnection`), já que não
  havia um SQL Server real disponível pra testar contra.

## Decisões importantes (pra não re-discutir do zero)

- Driver: **pyodbc** (confirmado wheel disponível pro Python 3.14 do venv).
  Requer "ODBC Driver 17/18 for SQL Server" instalado na máquina que roda o
  `.exe` — checado via `pyodbc.drivers()`, com mensagem clara se faltar.
- **Base modelo é obrigatória** na Criação de Base (no CriaBase original
  era opcional).
- **Para imediatamente no primeiro erro** durante o provisionamento (o
  CriaBase original só logava e continuava). Como consequência: se um passo
  anterior falhar, nenhum registro em `Parametros_Clientes` roda (nem no
  servidor modelo, nem no destino, nem no ServidorPP).
- ~~Registro duplo em produção + dev~~ — **substituído** (ver seção
  "Reformulação da Criação de Base" acima) pelo registro configurável em
  Parametros_Clientes: modelo / destino / os dois, sempre também no
  ServidorPP (100.77.102.1,1435), com dedup por servidor físico.
- Senha nunca é persistida em disco (nem a do login, nem as de
  modelo/destino/ServidorPP) — só servidor/usuário ficam salvos em
  `config.json` (`ultima_conexao`, `ultima_criacao_base`).

## Bug de Tkinter/Windows encontrado e corrigido

`Toplevel.transient(master)` quando `master` é uma janela `Tk()` escondida
com `.withdraw()` impede o Windows de criar uma janela nativa visível pro
diálogo (confirmado por reprodução mínima). Por isso `connection_dialog.py`
**não** chama `self.transient(master)` — só `grab_set()` (mantém a
modalidade sem o bug). Se algum dia trocar esse padrão de novo tela de
login, lembrar disso.

## Reformulação da Criação de Base (assistente de 5 etapas)

`src/gui/criar_base_panel.py` deixou de ser um formulário de uma tela só e
virou um assistente com indicador de etapas + navegação Voltar/Avançar,
tudo dentro de uma área rolável (`src/gui/scrollable_area.py`, extraído de
`excluir_contas_panel.py` pra ser reaproveitado):

1. **Servidores e base modelo** — servidor da base modelo e servidor de
   destino (onde a base nova é criada) agora podem ser DIFERENTES — antes
   era sempre o mesmo servidor, obrigatoriamente. Checkbox "É o mesmo
   servidor" espelha automaticamente modelo → destino quando marcado
   (padrão). Quando os servidores são o mesmo, a cópia de dados (03_dados.sql
   fixo e as tabelas extras da etapa 3) roda direto no SQL (cross-database,
   rápida); quando são diferentes, `criar_base_service.py` copia linha a
   linha via Python (lê da conexão do modelo, grava na de destino) — mais
   lenta, mas **não é mais pulada**: `schema_service.analisar_copia_fixa_de_dados`
   extrai do próprio `03_dados.sql` quais tabelas/colunas copiar (fonte
   única da verdade, nada duplicado à mão).
2. **Nova base e cartório** — Cidade/UF foram removidos do quadro "Nova
   base" e viraram campos de "Dados do cartório" (fazem mais sentido lá —
   são dados do cartório, não da base). DSN ODBC e Diretório de arquivos
   agora são sugeridos a partir do "Nome da base nova" (antes vinham de
   Cidade/UF, que não existem mais nessa etapa). "Responsável interino"
   mudou de lugar (antes ficava na seção "Regime e registro dev", que foi
   removida).
3. **Tabelas adicionais** (nova, opcional) — `src/services/schema_service.py`
   consulta `INFORMATION_SCHEMA.TABLES`/`COLUMNS` do banco modelo (via
   `?`-parametrizado) e deixa escolher tabelas e colunas extras pra copiar,
   além das ~15 tabelas fixas que `03_dados.sql` já cobre. Cada tabela
   marcada expande mostrando suas colunas (todas marcadas por padrão,
   individualmente desmarcáveis); colunas são buscadas sob demanda (lazy) só
   quando a tabela é marcada, com cache pra não repetir a consulta.
4. **Registro em Parametros_Clientes** (substituiu a antiga seção "Regime e
   registro dev/Pro-Packages") — os 13 campos reais da tabela
   `[dbo].[Parametros_Clientes]` (Nome, Servidor, Banco, Usuario, Senha,
   DiretorioArquivo, Odbc, BrowserDashboard, UrlDashboard, UrlDashboardToken,
   DiretorioMensalistas, UrlValidacao, **UrlGestorClientes** — esta última é
   NOVA, não existe no schema/template antigo, ver "Atenção" abaixo).
   Radio "ServidorPP (nosso) — 100.77.102.1,1435" x "Servidor do cliente"
   controla o valor padrão do campo Servidor. Banco/Usuario/Senha/
   DiretorioArquivo são sugeridos a partir da etapa 2 (nome da base/usuário/
   senha/diretório), e Odbc é calculado ao vivo como
   `DSN=ODBC_GF_{Nome};UID={Usuario};PWD={Senha};` — todos editáveis, com o
   mesmo padrão de "sugestão até editar manualmente" das outras auto-
   sugestões do painel. Um radio de 3 opções escolhe registrar só no
   servidor da base modelo, só no de destino, ou nos dois — e o ServidorPP
   é **sempre** incluído como alvo adicional (com suas próprias credenciais,
   reaproveitadas automaticamente se ServidorPP já for um dos outros dois
   servidores). Alvos com o mesmo servidor físico são deduplicados (um único
   INSERT), tanto a conexão quanto o registro.
5. **Confirmação e execução** — mesma barra de progresso/log de antes, só
   que agora reagindo a uma lista dinâmica de passos (pode incluir
   `tabelas_extras` e N passos `parametros_<alvo>`).

`src/services/criar_base_service.py` foi reescrito: `NovaBaseConfig` perdeu
`nome_dev`/`diretorio_dev`; entram `ParametrosClienteConfig`,
`AlvoParametros`, `TabelaExtra` e `PlanoProvisionamento` (empacota tudo que
`executar_criacao_base` precisa num só argumento). Conexões são reaproveitadas
por servidor (comparado por `servidor.strip().lower()`) — se dois alvos
apontam pro mesmo host físico, só uma conexão de verdade é aberta.

**Atenção pra quando for testar contra um banco real:** a coluna
`[UrlGestorClientes]` em `Parametros_Clientes` é nova — o schema real do
banco (em cada servidor: base modelo, destino, ServidorPP) provavelmente
ainda **não tem essa coluna**, e o INSERT vai falhar com "Invalid column
name" até ela ser adicionada manualmente em cada `Gestor_Parametros` real.

## Pendências / próximos passos

1. **Excluir Contas**: já implementado nesta sessão (não é mais placeholder)
   — consulta e permite excluir Contas/GrupoContábil/InterfaceContas/
   InterfaceArq/InterfaceComum/InterfaceFormaPgto/InterfaceHistorico
   existentes no banco. Ver `src/services/delete_service.py`.
2. **Testar contra um SQL Server real de teste** antes de qualquer uso em
   produção: login, "Executar no banco" em Criar Contas, "Excluir contas",
   e um provisionamento completo de Criação de Base — incluindo o caso de
   servidor modelo ≠ servidor de destino (cópia linha a linha via Python), a
   busca de tabelas/colunas extras (etapa 3), e o registro em
   Parametros_Clientes (lembrando de adicionar a coluna UrlGestorClientes
   antes, ver acima). Só foi validado com conexões falsas
   (`FakeConnection`/`FakeCursor`, testes automatizados e screenshots reais
   do app rodando) até agora — a cópia linha a linha em especial merece um
   teste contra um SQL Server real (volume de dados/tempo de execução).
3. Build do `.exe` (`build.bat`) ainda não foi re-executado com o `pyodbc`
   novo — `--add-data` pros templates `.sql` já foi adicionado, mas nunca
   foi testado empacotado (só `python app.py` direto do venv).
4. Automações "legais de ter" que ficaram só como ideia, não confirmadas
   com o usuário: presets por revenda (INR/Heros/Silvestrin) pra
   preencher `baseUsuario` automaticamente.

## Arquivos principais desta feature

```
app.py                                   # agora abre o login antes da MainWindow
src/gui/connection_dialog.py             # diálogo de login
src/gui/criar_base_panel.py              # painel da aba Criação de Base — assistente de 5 etapas
src/gui/excluir_contas_panel.py          # painel da aba Excluir Contas
src/gui/scrollable_area.py               # área rolável reaproveitada (Excluir Contas + Criação de Base)
src/gui/main_window.py                   # abas reais + "Executar no banco" + "Trocar cliente"
src/models/session.py                    # SessionContext
src/services/db_connection_service.py    # pyodbc: connect/listar bases/etc.
src/services/sql_batch_executor.py       # split GO + placeholders + stop-on-error
src/services/criar_base_service.py       # orquestra os passos de provisionamento (dinâmico)
src/services/schema_service.py           # introspecção de tabelas/colunas do banco modelo (etapa 3)
src/services/delete_service.py           # consultas/exclusões da aba Excluir Contas
src/services/settings_service.py         # persistência de conexão/criação de base (sem senha)
src/utils/constants.py                   # + resource_path(), SERVIDOR_PP
resources/sql_templates/criar_base/*.sql # copiados do CriaBase original
tests/test_sql_batch_executor.py
tests/test_criar_base_service.py
tests/test_schema_service.py
tests/test_delete_service.py
requirements.txt, build.bat              # + pyodbc, --add-data
```

Plano completo original (com todo o raciocínio de design): buscar no
histórico do Claude Code desta sessão, ou pedir pra eu regenerar um resumo
a partir deste arquivo — as decisões que importam já estão listadas acima.
