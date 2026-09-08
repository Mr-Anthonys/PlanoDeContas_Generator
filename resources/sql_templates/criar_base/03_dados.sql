use [$BASE_NOVA]
go

--begin tran
--rollback tran
--commit tran			

delete Resumo
delete Lançamentos
delete Lanca_exclui
delete InterfaceDataArq

-- GARANTIR QUE RELATORIOS E DADOSCARTORIO TENHAM APENAS UMA LINHA

insert into atualiza_redis_dash(
nome_tabela 
,[data]
)	
select 
nome_tabela 
,[data]
from [$BASE_MODELO].dbo.atualiza_redis_dash

insert into Bancos										
select * from [$BASE_MODELO].dbo.Bancos

insert into Contas										
(
Nome
,GrupoContábil
,Histórico
,[Tipo de Conta]
,[Forma de Transação]
,LOficial
,LGerencial
,LContábil
,LDinheiro
,LParticular
,LPrévio
,LPortal
,L_IRRF
,PDF
,Ativa
,ContrProt
,CodGProt
,GrupoPortal
,CodAux
)
select
Nome
,GrupoContábil
,Histórico
,[Tipo de Conta]
,[Forma de Transação]
,LOficial
,LGerencial
,LContábil
,LDinheiro
,LParticular
,LPrévio
,LPortal
,L_IRRF
,PDF
,Ativa
,ContrProt
,CodGProt
,GrupoPortal
,CodAux
from [$BASE_MODELO].dbo.Contas

insert into DadosCartorio								
(
RespTit
,RespNome
,RespCPF
,CartNome
,CartComarca
,CartEnd
,CartCid
,CartCEP
,CartBairro
,CartEst
,CartIR
,CartDeduzir
,LOficialNome1
,LOficialNome2
,LOficialSaldoI
,LOficialInicial
,LGerencialNome1
,LGerencialNome2
,LGerencialSaldoI
,LGerencialInicial
,LDinheiroNome1
,LDinheiroNome2
,LDinheiroSaldoI
,LDinheiroInicial
,LParticularNome1
,LParticularNome2
,LParticularSaldoI
,LParticularInicial
,LPrévioNome1
,LPrévioNome2
,LPrévioSaldoI
,LPrévioInicial
,LOficialMêsSaldoI
,LGerencialMêsSaldoI
,LDinheiroMêsSaldoI
,LParticularMêsSaldoI
,LPrévioMêsSaldoI
,LOficialAnoSaldoI
,LGerencialAnoSaldoI
,LDinheiroAnoSaldoI
,LParticularAnoSaldoI
,LPrévioAnoSaldoI
,LOficialNovaPágina
,LGerencialNovaPágina
,LDinheiroNovaPágina
,LParticularNovaPágina
,LPrévioNovaPágina
,LOficialHistórico
,LPortalDNome1
,LGerencialHistórico
,LPortalDNome2
,LDinheiroHistórico
,LPortalRNome1
,LParticularHistórico
,LPortalRNome2
,LPrévioHistórico
,TipoPortal
,L_IRRFNome1
,L_IRRFNome2
,L_IRRFSaldoI
,L_IRRFMêsSaldoI
,L_IRRFAnoSaldoI
,L_IRRFNovaPágina
,L_IRRFHistórico
,L_IRRFInicial
,L_IRRFResIR
,LOficialResIR
,PaginaResumos
,L_IRRFDedu
,LOficialDedu
,ConciDeb
,ConciCred
,ConciDepDin
,ConciChqCancel
,ChqEmConciData
,Exclui_PDF_Orig
,LGerencialZeraSaldo
,LParticularZeraSaldo
,ConciChqExtr
,Edital
,Intimacao
,Telegrama
,TipoCustasPortal
,LOficialFormaEmol
,L_IRRFFormaEmol
,L_IRRFSomaEmol
,L_IRRFTextEmol
,LGerencialFormaEmol
,L_IRRFSomaEmolTipo
,L_IRRFSomaEmolGrupo
,L_IRRFSomaEmolImprime
,L_IRRFTextEmolHist
,LOficialLNum
,L_IRRFLNum
,LOficialFormaEmolDesp
,L_IRRFFormaEmolDesp
,LPartFormaEmol
,LPartFormaEmolDesp
,CartCNPJ
,livro_diario_cpf_cnpj
,livro_caixa_cpf_cnpj
,L_IRRF_TipoEmol
,ContTit
,ContNome
,ContCPF
,ContCRC
,LOficial_ResAssina
,L_IRRF_ResAssina
,DataHoraPortal
,livro_gerenc_cpf_cnpj
,LOficialLimPag
,LOficialFrenteVerso
,LOficialPagLayout
,L_IRRFLimPag
,L_IRRFFrenteVerso
,L_IRRFPagLayout
,LGerencialFrenteVerso
,LGerencialPagLayout
,GifVago
,GifCns
,GifUrlToken
,GifClientId
,GifClientSecret
,GifScope
,GifDataInicio
,GifUrlEnvio
,GifTokenDeHomologacao
)
select
RespTit
,RespNome
,RespCPF
,CartNome
,CartComarca
,CartEnd
,CartCid
,CartCEP
,CartBairro
,CartEst
,CartIR
,CartDeduzir
,LOficialNome1
,LOficialNome2
,LOficialSaldoI
,LOficialInicial
,LGerencialNome1
,LGerencialNome2
,LGerencialSaldoI
,LGerencialInicial
,LDinheiroNome1
,LDinheiroNome2
,LDinheiroSaldoI
,LDinheiroInicial
,LParticularNome1
,LParticularNome2
,LParticularSaldoI
,LParticularInicial
,LPrévioNome1
,LPrévioNome2
,LPrévioSaldoI
,LPrévioInicial
,LOficialMêsSaldoI
,LGerencialMêsSaldoI
,LDinheiroMêsSaldoI
,LParticularMêsSaldoI
,LPrévioMêsSaldoI
,LOficialAnoSaldoI
,LGerencialAnoSaldoI
,LDinheiroAnoSaldoI
,LParticularAnoSaldoI
,LPrévioAnoSaldoI
,LOficialNovaPágina
,LGerencialNovaPágina
,LDinheiroNovaPágina
,LParticularNovaPágina
,LPrévioNovaPágina
,LOficialHistórico
,LPortalDNome1
,LGerencialHistórico
,LPortalDNome2
,LDinheiroHistórico
,LPortalRNome1
,LParticularHistórico
,LPortalRNome2
,LPrévioHistórico
,TipoPortal
,L_IRRFNome1
,L_IRRFNome2
,L_IRRFSaldoI
,L_IRRFMêsSaldoI
,L_IRRFAnoSaldoI
,L_IRRFNovaPágina
,L_IRRFHistórico
,L_IRRFInicial
,L_IRRFResIR
,LOficialResIR
,PaginaResumos
,L_IRRFDedu
,LOficialDedu
,ConciDeb
,ConciCred
,ConciDepDin
,ConciChqCancel
,ChqEmConciData
,Exclui_PDF_Orig
,LGerencialZeraSaldo
,LParticularZeraSaldo
,ConciChqExtr
,Edital
,Intimacao
,Telegrama
,TipoCustasPortal
,LOficialFormaEmol
,L_IRRFFormaEmol
,L_IRRFSomaEmol
,L_IRRFTextEmol
,LGerencialFormaEmol
,L_IRRFSomaEmolTipo
,L_IRRFSomaEmolGrupo
,L_IRRFSomaEmolImprime
,L_IRRFTextEmolHist
,LOficialLNum
,L_IRRFLNum
,LOficialFormaEmolDesp
,L_IRRFFormaEmolDesp
,LPartFormaEmol
,LPartFormaEmolDesp
,CartCNPJ
,livro_diario_cpf_cnpj
,livro_caixa_cpf_cnpj
,L_IRRF_TipoEmol
,ContTit
,ContNome
,ContCPF
,ContCRC
,LOficial_ResAssina
,L_IRRF_ResAssina
,DataHoraPortal
,livro_gerenc_cpf_cnpj
,LOficialLimPag
,LOficialFrenteVerso
,LOficialPagLayout
,L_IRRFLimPag
,L_IRRFFrenteVerso
,L_IRRFPagLayout
,LGerencialFrenteVerso
,LGerencialPagLayout
,GifVago
,GifCns
,GifUrlToken
,GifClientId
,GifClientSecret
,GifScope
,GifDataInicio
,GifUrlEnvio
,GifTokenDeHomologacao
from [$BASE_MODELO].dbo.DadosCartorio

insert into DadosIR										
(
Ano
,Mês
,AnoMês
,MêsNum
,ValorP
,ValorRS
,Lista
,MaxFaixa
)
select
Ano
,Mês
,AnoMês
,MêsNum
,ValorP
,ValorRS
,Lista
,MaxFaixa
from [$BASE_MODELO].dbo.DadosIR

insert into DatabaseVersion								
(
[Version]
,IsUpdating
)
select
[Version]
,IsUpdating
from [$BASE_MODELO].dbo.DatabaseVersion

insert into Deducoes									
(
Tipo
,Ano
,Mês
,AnoMês
,MêsNum
,Descrição
,Valor
)
select
Tipo
,Ano
,Mês
,AnoMês
,MêsNum
,Descrição
,Valor
from [$BASE_MODELO].dbo.Deducoes

insert into Flags										
(
CampoI
,CampoV
,CampoU
,CampoB
--,Cartorio_id
)
select
CampoI
,CampoV
,CampoU
,CampoB
--,Cartorio_id
from [$BASE_MODELO].dbo.Flags

insert into GrupoContábil								
(
Nome
)
select
Nome
from [$BASE_MODELO].dbo.GrupoContábil

insert into GrupoPortal									
(
CodGrupoPortal
,TipoGrupo
,NomeGrupo
,UF
)
select
CodGrupoPortal
,TipoGrupo
,NomeGrupo
,UF
from [$BASE_MODELO].dbo.GrupoPortal

insert into InterfaceArq								
(
NomeTipo
,Extensão
,FormaColunas
,LocalArquivos
,Linha1
,LinhaF
,LimpaCol
,Cab_Ult_Col
,Cab_Ult_Text
,Rod_Pri_Col
,Rod_Pri_Text
,InterfaceInicial
,Cab_Ult_Oco
,Rod_Pri_Oco
,InterfaceEntrManual
)
select
NomeTipo
,Extensão
,FormaColunas
,LocalArquivos
,Linha1
,LinhaF
,LimpaCol
,Cab_Ult_Col
,Cab_Ult_Text
,Rod_Pri_Col
,Rod_Pri_Text
,InterfaceInicial
,Cab_Ult_Oco
,Rod_Pri_Oco
,InterfaceEntrManual
from [$BASE_MODELO].dbo.InterfaceArq

insert into InterfaceComum								
(
LocalCodigo
,LocalDataMovimento
,LocalValor
,LocalForma
,LocalAtos
,LocalVlBruto
,LocalEstado
,LocalIPESP
,LocalStaCasa
,LocalRegCivil
,LocalTribunal
,TipoArq
,LocalISS
,LocalMP
,LocalEdital
,LocalIntimacao
,LocalTelegrama
,LocalProtocolo
)
select
LocalCodigo
,LocalDataMovimento
,LocalValor
,LocalForma
,LocalAtos
,LocalVlBruto
,LocalEstado
,LocalIPESP
,LocalStaCasa
,LocalRegCivil
,LocalTribunal
,TipoArq
,LocalISS
,LocalMP
,LocalEdital
,LocalIntimacao
,LocalTelegrama
,LocalProtocolo
from [$BASE_MODELO].dbo.InterfaceComum

insert into InterfaceContas								
(
ContaOrigem
,ContaSGF
,ContaInterID
,TipoArq
,CodCC
,CodUN
)
select
ContaOrigem
,ContaSGF
,ContaInterID
,TipoArq
,CodCC
,CodUN
from [$BASE_MODELO].dbo.InterfaceContas

insert into InterfaceFormaPgto							
(
FormaID
,FormaSist
,FormaSGF
,BcoSGF
,CCNumSGF
,TipoArq
,ChequeSGF
,ChequeSGFIni
,ChequeSGFTam
,ChequeSGFFim
)
select
FormaID
,FormaSist
,FormaSGF
,BcoSGF
,CCNumSGF
,TipoArq
,ChequeSGF
,ChequeSGFIni
,ChequeSGFTam
,ChequeSGFFim
from [$BASE_MODELO].dbo.InterfaceFormaPgto

insert into InterfaceHistorico							
(
ContaOrigem
,Precedente1
,Historico1
,Precedente2
,Historico2
,Precedente3
,Historico3
,Precedente4
,Historico4
,Precedente5
,Historico5
,Precedente6
,Historico6
,Precedente7
,Historico7
,Precedente8
,Historico8
,TipoArq
,HistIni1
,HistTam1
,HistFim1
,HistIni2
,HistTam2
,HistFim2
,HistIni3
,HistTam3
,HistFim3
,HistIni4
,HistTam4
,HistFim4
,HistIni5
,HistTam5
,HistFim5
,HistIni6
,HistTam6
,HistFim6
,HistIni7
,HistTam7
,HistFim7
,HistIni8
,HistTam8
,HistFim8
)
select
ContaOrigem
,Precedente1
,Historico1
,Precedente2
,Historico2
,Precedente3
,Historico3
,Precedente4
,Historico4
,Precedente5
,Historico5
,Precedente6
,Historico6
,Precedente7
,Historico7
,Precedente8
,Historico8
,TipoArq
,HistIni1
,HistTam1
,HistFim1
,HistIni2
,HistTam2
,HistFim2
,HistIni3
,HistTam3
,HistFim3
,HistIni4
,HistTam4
,HistFim4
,HistIni5
,HistTam5
,HistFim5
,HistIni6
,HistTam6
,HistFim6
,HistIni7
,HistTam7
,HistFim7
,HistIni8
,HistTam8
,HistFim8
from [$BASE_MODELO].dbo.InterfaceHistorico

insert into Relatório									
(
Livro
,Mês
,SaldoInicial
,CCNum
,BcoNome
,FolhaInicial
,PapelTamanho
,Ano
,NomeEntrada
,NomeSaida
,NovaPagConcExtr
,RelUpper
,FormatoRelAlt
,LivroNum
,FormatoRelLivro
,AjusteMargem
)
select
Livro
,Mês
,SaldoInicial
,CCNum
,BcoNome
,FolhaInicial
,PapelTamanho
,Ano
,NomeEntrada
,NomeSaida
,NovaPagConcExtr
,RelUpper
,FormatoRelAlt
,LivroNum
,FormatoRelLivro
,AjusteMargem
from [$BASE_MODELO].dbo.Relatório

insert into Resumo										
(
Ano
,Mês
,Livro
,SaldoInicial
,SaldoFinal
,PaginaInicial
,PaginaFinal
,BcoNome
,CCNum
,Entradas
,Saidas
,MêsNum
,FormaEmol
,SomaEmol
,TextEmol
,SomaEmolTipo
,SomaEmolGrupo
,SomaEmolImprime
,TextEmolHist
,LivroNum
,FormaEmolDesp
,L_IRRF_TipoEmol
,LivroLimPag
,LivroFrenteVerso
,LivroPagLayout
,FormatoRelLivro
,LivroCPF_CNPJ
)
select
Ano
,Mês
,Livro
,SaldoInicial
,SaldoFinal
,PaginaInicial
,PaginaFinal
,BcoNome
,CCNum
,Entradas
,Saidas
,MêsNum
,FormaEmol
,SomaEmol
,TextEmol
,SomaEmolTipo
,SomaEmolGrupo
,SomaEmolImprime
,TextEmolHist
,LivroNum
,FormaEmolDesp
,L_IRRF_TipoEmol
,LivroLimPag
,LivroFrenteVerso
,LivroPagLayout
,FormatoRelLivro
,LivroCPF_CNPJ
from [$BASE_MODELO].dbo.Resumo

insert into Usuário										
(
Usuário
,PapelTamanho
,SGFPrinter
,Senha
,CamposRelCDT
,email
,VersaoBase
,Privilégios
)
select
Usuário
,PapelTamanho
,SGFPrinter
,Senha
,CamposRelCDT
,email
,VersaoBase
,Privilégios
from [$BASE_MODELO].dbo.Usuário

--insert into Assist_Extrato			select * from [$BASE_MODELO].dbo.Assist_Extrato
--insert into Assist_Gestor				select * from [$BASE_MODELO].dbo.Assist_Gestor
--insert into Assist_Grid				select * from [$BASE_MODELO].dbo.Assist_Grid
--insert into AssistDetalhe				select * from [$BASE_MODELO].dbo.AssistDetalhe
--insert into AssistItens				select * from [$BASE_MODELO].dbo.AssistItens
--insert into AssistResumo				select * from [$BASE_MODELO].dbo.AssistResumo
--insert into CDT						select * from [$BASE_MODELO].dbo.CDT
--insert into CDT_Rel					select * from [$BASE_MODELO].dbo.CDT_Rel
--insert into CDT_RelLista				select * from [$BASE_MODELO].dbo.CDT_RelLista
--insert into CDT_Temp					select * from [$BASE_MODELO].dbo.CDT_Temp
--insert into CentrosdeCusto			select * from [$BASE_MODELO].dbo.CentrosdeCusto
--insert into ChequesContasRecorrentes	select * from [$BASE_MODELO].dbo.ChequesContasRecorrentes
--insert into ChequesTesouraria			select * from [$BASE_MODELO].dbo.ChequesTesouraria
--insert into ConciBanco				select * from [$BASE_MODELO].dbo.ConciBanco
--insert into ConsContas				select * from [$BASE_MODELO].dbo.ConsContas
--insert into ConsLança					select * from [$BASE_MODELO].dbo.ConsLança
--insert into ConsProtocolo				select * from [$BASE_MODELO].dbo.ConsProtocolo
--insert into ContasRecorrentes			select * from [$BASE_MODELO].dbo.ContasRecorrentes
--insert into Contratos					select * from [$BASE_MODELO].dbo.Contratos
--insert into ControleProtocolo			select * from [$BASE_MODELO].dbo.ControleProtocolo
--insert into CustasRelCaixaIR			select * from [$BASE_MODELO].dbo.CustasRelCaixaIR
--insert into DeduHist					select * from [$BASE_MODELO].dbo.DeduHist
--insert into DepósitoPrévio			select * from [$BASE_MODELO].dbo.DepósitoPrévio
--insert into EspExtrato				select * from [$BASE_MODELO].dbo.EspExtrato
--insert into EspGestor					select * from [$BASE_MODELO].dbo.EspGestor
--insert into IntensEspTemp				select * from [$BASE_MODELO].dbo.IntensEspTemp
--insert into InterfaceCheque			select * from [$BASE_MODELO].dbo.InterfaceCheque
--insert into InterfaceExtrato			select * from [$BASE_MODELO].dbo.InterfaceExtrato
--insert into InterfaceExtratoComp		select * from [$BASE_MODELO].dbo.InterfaceExtratoComp
--insert into InterfaceExtratoGrid		select * from [$BASE_MODELO].dbo.InterfaceExtratoGrid
--insert into InterfaceExtratoTarifa	select * from [$BASE_MODELO].dbo.InterfaceExtratoTarifa
--insert into log_gestor				select * from [$BASE_MODELO].dbo.log_gestor
--insert into Movimento					select * from [$BASE_MODELO].dbo.Movimento
--insert into PreLancamento				select * from [$BASE_MODELO].dbo.PreLancamento
--insert into RateioCC_Conta			select * from [$BASE_MODELO].dbo.RateioCC_Conta				
--insert into RateioCC_Lança			select * from [$BASE_MODELO].dbo.RateioCC_Lança
--insert into RateioCC_Temp				select * from [$BASE_MODELO].dbo.RateioCC_Temp
--insert into RateioUN_Conta			select * from [$BASE_MODELO].dbo.RateioUN_Conta
--insert into RateioUN_Lança			select * from [$BASE_MODELO].dbo.RateioUN_Lança
--insert into RateioUN_Temp				select * from [$BASE_MODELO].dbo.RateioUN_Temp
--insert into SaldoAtual				select * from [$BASE_MODELO].dbo.SaldoAtual
--insert into tipo_entrada_mov_caixa	select * from [$BASE_MODELO].dbo.tipo_entrada_mov_caixa
--insert into UnidadeNegocio			select * from [$BASE_MODELO].dbo.UnidadeNegocio
--insert into ValidaMes					select * from [$BASE_MODELO].dbo.ValidaMes
			
----insert into ConciExtrato			select * from [$BASE_MODELO].dbo.ConciExtrato				
----insert into ConciMoney				select * from [$BASE_MODELO].dbo.ConciMoney				
----insert into ConfigControleProtocolo	select * from [$BASE_MODELO].dbo.ConfigControleProtocolo	
----insert into ContasProt				select * from [$BASE_MODELO].dbo.ContasProt		

----insert into [Card]					select * from [$BASE_MODELO].dbo.[Card]						
----insert into CardV2					select * from [$BASE_MODELO].dbo.CardV2				
----insert into InterfaceDataArq		select * from [$BASE_MODELO].dbo.InterfaceDataArq	
----insert into Lanca_exclui			select * from [$BASE_MODELO].dbo.Lanca_exclui				
----insert into Lançamentos				select * from [$BASE_MODELO].dbo.Lançamentos				
----insert into LançaRel				select * from [$BASE_MODELO].dbo.LançaRel							
----insert into scores					select * from [$BASE_MODELO].dbo.scores						
----insert into tbl_tmp_despesas		select * from [$BASE_MODELO].dbo.tbl_tmp_despesas			
----insert into TempRel					select * from [$BASE_MODELO].dbo.TempRel			

----delete from Assist_Extrato				
----delete from Assist_Gestor				
----delete from Assist_Grid					
----delete from AssistDetalhe				
----delete from AssistItens					
----delete from AssistResumo				
----delete from atualiza_redis_dash			
----delete from Bancos						
----delete from [Card]						
----delete from CardV2						
----delete from CDT							
----delete from CDT_Rel						
----delete from CDT_RelLista				
----delete from CDT_Temp					
----delete from CentrosdeCusto				
----delete from ChequesContasRecorrentes	
----delete from ChequesTesouraria			
----delete from ConciBanco					
------delete from ConciExtrato				
------delete from ConciMoney				
------delete from ConfigControleProtocolo	
----delete from ConsContas					
----delete from ConsLança					
----delete from ConsProtocolo				
----delete from Contas						
------delete from ContasProt				
----delete from ContasRecorrentes			
----delete from Contratos					
----delete from ControleProtocolo			
----delete from CustasRelCaixaIR			
----delete from DadosCartorio				
----delete from DadosIR						
----delete from DatabaseVersion				
----delete from Deducoes					
----delete from DeduHist					
----delete from DepósitoPrévio				
----delete from EspExtrato					
----delete from EspGestor					
----delete from Flags						
----delete from GrupoContábil				
----delete from GrupoPortal					
----delete from IntensEspTemp				
----delete from InterfaceArq				
----delete from InterfaceCheque				
----delete from InterfaceComum				
----delete from InterfaceContas				
------delete from InterfaceDataArq			
----delete from InterfaceExtrato			
----delete from InterfaceExtratoComp		
----delete from InterfaceExtratoGrid		
----delete from InterfaceExtratoTarifa		
----delete from InterfaceFormaPgto			
----delete from InterfaceHistorico			
------delete from Lanca_exclui				
------delete from Lançamentos				
------delete from LançaRel					
----delete from log_gestor					
----delete from Movimento					
----delete from PreLancamento				
----delete from RateioCC_Conta				
----delete from RateioCC_Lança				
----delete from RateioCC_Temp				
----delete from RateioUN_Conta				
----delete from RateioUN_Lança				
----delete from RateioUN_Temp				
----delete from Relatório					
----delete from Resumo						
----delete from SaldoAtual					
----delete from scores						
------delete from tbl_tmp_despesas			
------delete from TempRel					
----delete from tipo_entrada_mov_caixa		
----delete from UnidadeNegocio				
----delete from Usuário						
----delete from ValidaMes	
