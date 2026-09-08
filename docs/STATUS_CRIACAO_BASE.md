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
  em produção falhar, o registro em `Gestor_Parametros` de **dev também não
  roda** (lá sempre rodava por último, independente do resultado).
- Mantido o **registro duplo** em `Gestor_Parametros` (produção + dev) —
  pedido explícito do usuário ("um servidor é pro cliente, o dev é pra
  nós").
- Senha nunca é persistida em disco (nem a do login, nem a do servidor
  dev) — só servidor/usuário ficam salvos em `config.json`
  (`ultima_conexao`, `ultima_criacao_base`).
- `$HOST` no registro de dev continua usando o endereço do servidor de
  **produção** (igual ao CriaBase original) — é o mesmo banco físico do
  cliente nos dois registros, só a base `Gestor_Parametros` de destino
  muda.

## Bug de Tkinter/Windows encontrado e corrigido

`Toplevel.transient(master)` quando `master` é uma janela `Tk()` escondida
com `.withdraw()` impede o Windows de criar uma janela nativa visível pro
diálogo (confirmado por reprodução mínima). Por isso `connection_dialog.py`
**não** chama `self.transient(master)` — só `grab_set()` (mantém a
modalidade sem o bug). Se algum dia trocar esse padrão de novo tela de
login, lembrar disso.

## Pendências / próximos passos

1. **Excluir Contas**: não existe spec em lugar nenhum (nem no Python, nem
   no CriaBase C#). Precisa ser definida do zero antes de implementar —
   hoje é só um placeholder.
2. **Testar contra um SQL Server real de teste** antes de qualquer uso em
   produção: login, "Executar no banco" em Criar Contas, e um
   provisionamento completo de Criação de Base (incluindo forçar um erro no
   meio de propósito pra confirmar que para e reporta certo). Só foi
   validado com conexões falsas (`FakeConnection`/`FakeCursor`) até agora.
3. Build do `.exe` (`build.bat`) ainda não foi re-executado com o `pyodbc`
   novo — `--add-data` pros templates `.sql` já foi adicionado, mas nunca
   foi testado empacotado (só `python app.py` direto do venv).
4. Automações "legais de ter" que ficaram só como ideia, não confirmadas
   com o usuário: presets por revenda (INR/Heros/Silvestrin) pra
   preencher `baseUsuario`/servidor dev automaticamente.

## Arquivos principais desta feature

```
app.py                                   # agora abre o login antes da MainWindow
src/gui/connection_dialog.py             # novo — diálogo de login
src/gui/criar_base_panel.py              # novo — painel da aba Criação de Base
src/gui/main_window.py                   # abas reais + "Executar no banco"
src/models/session.py                    # novo — SessionContext
src/services/db_connection_service.py    # novo — pyodbc: connect/listar bases/etc.
src/services/sql_batch_executor.py       # novo — split GO + placeholders + stop-on-error
src/services/criar_base_service.py       # novo — orquestra os 7 passos
src/services/settings_service.py         # + persistência de conexão/dev (sem senha)
src/utils/constants.py                   # + resource_path() (sys._MEIPASS)
resources/sql_templates/criar_base/*.sql # copiados do CriaBase original
tests/test_sql_batch_executor.py         # novo
tests/test_criar_base_service.py         # novo
requirements.txt, build.bat              # + pyodbc, --add-data
```

Plano completo original (com todo o raciocínio de design): buscar no
histórico do Claude Code desta sessão, ou pedir pra eu regenerar um resumo
a partir deste arquivo — as decisões que importam já estão listadas acima.
