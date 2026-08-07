# Regras de negócio identificadas

Levantamento feito a partir da análise célula a célula (valores e fórmulas) de:

* `Documentacao_Plano_de_Contas_Receitas_Atualizada.docx`
* `PLANO DE CONTAS - RECEITAS.xlsx` (modelo em branco)
* `Plano de Contas Receitas - Conchas.xlsx` (exemplo real preenchido, 31 contas)

## 1. Schema das 8 tabelas

| Tabela | Colunas (ordem exata) |
|---|---|
| `Contas` | Nome, GrupoContábil, Histórico, Tipo de Conta, Forma de Transação, LOficial, LGerencial, LContábil, LDinheiro, LParticular, LPrévio, LPortal, GrupoPortal, L_IRRF, PDF, Ativa |
| `GrupoPortal` | NomeGrupo, TipoGrupo (CodGrupoPortal e UF não entram no INSERT) |
| `GrupoContábil` | Nome |
| `InterfaceContas` | ContaSGF, ContaOrigem, TipoArq |
| `InterfaceHistorico` | ContaOrigem, Historico1, Historico2, TipoArq + 38 colunas fixas (HistIni1..8/HistTam1..8/HistFim1..8 = 0; Precedente1..8/Historico3..8 = '') |
| `InterfaceArq` | NomeTipo, Extensão, FormaColunas, LocalArquivos, Linha1, LinhaF, LimpaCol, Cab_Ult_Col, Cab_Ult_Text, Rod_Pri_Col, Rod_Pri_Text, InterfaceInicial, Cab_Ult_Oco, Rod_Pri_Oco, InterfaceEntrManual |
| `InterfaceComum` | LocalCodigo, LocalDataMovimento, LocalValor, LocalForma, LocalAtos, LocalVlBruto, LocalEstado, LocalIPESP, LocalStaCasa, LocalRegCivil, LocalTribunal, TipoArq, LocalISS, LocalMP, LocalEdital, LocalIntimacao, LocalTelegrama, LocalProtocolo |
| `InterfaceFormaPgto` | FormaSist, FormaSGF, BcoSGF, CCNumSGF, TipoArq, ChequeSGF, ChequeSGFIni, ChequeSGFTam, ChequeSGFFim |

## 2. ContaOrigem é sempre string entre aspas

Nas fórmulas de `InterfaceContas` e `InterfaceHistorico`, tanto no modelo quanto no Conchas, `ContaOrigem` é montado com `CONCATENATE("'", valor, "',")` — ou seja, mesmo a célula contendo um número puro (1, 2, 3...), o SQL final sempre grava o código entre aspas simples. O aplicativo reproduz esse comportamento e preserva zeros à esquerda quando o código for informado como texto.

## 3. Bug confirmado em GrupoPortal

Fórmula original: `=CONCATENATE(C75,"')")`, onde `C75` (TipoGrupo) é numérico. Isso gera `VALUES('NOME',0')` — um apóstrofo indevido após o número, que quebra a string SQL. Confirmado idêntico no modelo e no Conchas. **Corrigido** no gerador para `VALUES('NOME',0)`.

## 4. Grupos: derivação automática (correção de inconsistência)

No Conchas, das 31 contas: 15 usam `TABELIONATO DE NOTAS` e 16 usam `PROTESTO`. Porém as seções manuais de `GrupoPortal`/`GrupoContábil` cadastravam `TABELIONATO DE NOTAS` e `REGISTRO CIVIL` — ou seja, `PROTESTO` nunca era criado (16 contas ficariam com grupo inexistente) e `REGISTRO CIVIL` era criado sem nunca ser usado. **Corrigido**: o aplicativo deriva os grupos de `GrupoPortal`/`GrupoContábil` automaticamente a partir dos grupos realmente usados pelas contas importadas, eliminando essa classe de erro por construção.

## 5. Histórico com um ou dois marcadores `@`

`Contas.Histórico` guarda o texto-base com até 2 marcadores `@`, sem nunca ser alterado pela importação futura. `InterfaceHistorico.Historico1`/`Historico2` armazenam apenas os **nomes das colunas** (ex.: `Qtd`, `Protocolo`, `LivroFolha`) que substituirão os marcadores, na ordem em que aparecem (posicional). No Conchas, todas as 31 contas usam o mesmo texto com 1 marcador (`EMOLUMENTOS RECEBIDOS - QTD DE ATOS @`), mas o valor de `Historico1` gravado é literalmente a string `"Historico"` — que não corresponde a nenhuma coluna de `InterfaceComum`. Isso foi identificado como um **erro de preenchimento no arquivo original**, não como um padrão a reproduzir (ver README, seção "Correções realizadas").

## 6. Aba Interface já tem os 3 conjuntos de TipoArq

`Emolumentos`, `Emolumentos_Protesto` e `Emolumentos_Notas` já existem completos (InterfaceArq + InterfaceComum + InterfaceFormaPgto) tanto no modelo quanto no Conchas, com conteúdo idêntico entre si a menos do próprio nome do TipoArq. Esses três conjuntos foram extraídos para `config.json` como fonte única de verdade.

## 7. Falta de proteção contra duplicidade

No processo manual, somente `Contas` possuía `IF NOT EXISTS` antes do INSERT. As outras 7 tabelas não tinham essa proteção. **Corrigido**: todos os 8 processos gerados pelo aplicativo incluem `IF NOT EXISTS`.

## 8. Ordem lógica de execução

`GrupoPortal`/`GrupoContábil` → `Contas` → `InterfaceArq`/`InterfaceComum`/`InterfaceFormaPgto` → `InterfaceContas` → `InterfaceHistorico`. Essa é a ordem usada na aba "Script completo".
