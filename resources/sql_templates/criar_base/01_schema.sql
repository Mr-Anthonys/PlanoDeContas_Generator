USE [master]
GO
CREATE DATABASE [$BASE_NOVA]
GO
-- ALTER DATABASE [$BASE_NOVA] SET COMPATIBILITY_LEVEL = 140
-- GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [$BASE_NOVA].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
-- ALTER DATABASE [$BASE_NOVA] SET ANSI_NULL_DEFAULT OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET ANSI_NULLS OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET ANSI_PADDING OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET ANSI_WARNINGS OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET ARITHABORT OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET AUTO_CLOSE OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET AUTO_SHRINK OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET AUTO_UPDATE_STATISTICS ON 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET CURSOR_CLOSE_ON_COMMIT OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET CURSOR_DEFAULT  GLOBAL 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET CONCAT_NULL_YIELDS_NULL OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET NUMERIC_ROUNDABORT OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET QUOTED_IDENTIFIER OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET RECURSIVE_TRIGGERS OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET  DISABLE_BROKER 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET DATE_CORRELATION_OPTIMIZATION OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET TRUSTWORTHY OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET ALLOW_SNAPSHOT_ISOLATION OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET PARAMETERIZATION SIMPLE 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET READ_COMMITTED_SNAPSHOT OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET HONOR_BROKER_PRIORITY OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET RECOVERY FULL 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET  MULTI_USER 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET PAGE_VERIFY CHECKSUM  
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET DB_CHAINING OFF 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET TARGET_RECOVERY_TIME = 60 SECONDS 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET DELAYED_DURABILITY = DISABLED 
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET ACCELERATED_DATABASE_RECOVERY = OFF  
-- GO
-- ALTER DATABASE [$BASE_NOVA] SET QUERY_STORE = OFF
-- GO
USE [$BASE_NOVA]
GO

 CREATE function [dbo].[diaVencimentoContaAPagar](@diaVencimento as  int)                                                      
 Returns datetime                                                                                                              
 as                                                                                                                            
 begin                                                                                                                         
                                                                                                                               
                                                                                                                               
   declare @DataVencimento as datetime =    DATEFROMPARTS( datepart(yyyy,getdate()), datepart(MONTH,getdate()),@diaVencimento) 
   declare @Vencimento as int                                                                                                  
   set @Vencimento = @diaVencimento                                                                                            
                                                                                                                               
                                                                                                                               
                                                                                                                               
   IF datepart(day,getdate())  > @diaVencimento                                                                                
   BEGIN                                                                                                                       
                                                                                                                               
    SET @DataVencimento =  DATEADD(MONTH,1,@DataVencimento)                                                                    
                                                                                                                               
                                                                                                                               
   END                                                                                                                         
                                                                                                                               
                                                                                                                               
   return @DataVencimento                                                                                                      
 end                                                                                                                           
GO
/****** Object:  Table [dbo].[Lançamentos]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Lançamentos](
	[DataMov] [datetime] NOT NULL,
	[DataLança] [datetime] NULL,
	[ContaLança] [varchar](80) NULL,
	[GrupoLança] [varchar](80) NULL,
	[TipoLança] [nvarchar](30) NULL,
	[FormaLança] [nvarchar](20) NULL,
	[LOficialLança] [bit] NOT NULL,
	[LGerencialLança] [bit] NOT NULL,
	[LBancoLança] [bit] NOT NULL,
	[ValorLança] [money] NULL,
	[CCNumLança] [nvarchar](15) NULL,
	[BcoNomeLança] [nvarchar](30) NULL,
	[ChqLança] [nvarchar](15) NULL,
	[ValorDébito] [money] NULL,
	[ValorCrédito] [money] NULL,
	[LançaID] [int] IDENTITY(1,1) NOT NULL,
	[LDinheiroLança] [bit] NOT NULL,
	[LParticularLança] [bit] NOT NULL,
	[LPrévioLança] [smallint] NULL,
	[Conciliado] [nvarchar](1) NULL,
	[LPortalLança] [bit] NOT NULL,
	[NumeroAtosLança] [smallint] NULL,
	[ValorBrutoLança] [money] NULL,
	[ValorEstado] [money] NULL,
	[ValorIPESP] [money] NULL,
	[ValorCivil] [money] NULL,
	[ValorTribunal] [money] NULL,
	[ValorStaCasa] [money] NULL,
	[HistLança] [varchar](max) NULL,
	[UserLança] [nvarchar](20) NULL,
	[L_IRRFLança] [bit] NULL,
	[ValorISS] [money] NULL,
	[ValorMP] [money] NULL,
	[PdfNF] [nvarchar](50) NULL,
	[PdfComp] [nvarchar](50) NULL,
	[DataConci] [datetime] NULL,
	[ValorEdital] [money] NULL,
	[ValorIntimacao] [money] NULL,
	[ValorTelegrama] [money] NULL,
	[flag_data] [datetime] NULL,
	[flag_tipo] [nvarchar](1) NULL,
	[statusPreLancamento] [varchar](30) NULL,
	[ContaRecorrenteId] [int] NULL,
	[PreLancamentoId] [int] NULL,
	[ProtNumero] [varchar](50) NULL,
	[GrupoPortalLança] [varchar](80) NULL,
	[DataEnvio] [date] NULL,
	[StatusEnvio] [smallint] NULL,
	[ProtocoloEnvio] [uniqueidentifier] NULL,
	[ObservacoesEnvio] [varchar](200) NULL,
PRIMARY KEY CLUSTERED 
(
	[LançaID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Contas]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Contas](
	[Nome] [varchar](80) NULL,
	[GrupoContábil] [varchar](80) NULL,
	[Histórico] [varchar](max) NULL,
	[Tipo de Conta] [nvarchar](25) NULL,
	[Forma de Transação] [nvarchar](20) NULL,
	[LOficial] [bit] NOT NULL,
	[LGerencial] [bit] NOT NULL,
	[LContábil] [bit] NOT NULL,
	[LDinheiro] [bit] NOT NULL,
	[LParticular] [bit] NOT NULL,
	[LPrévio] [smallint] NULL,
	[LPortal] [bit] NOT NULL,
	[L_IRRF] [bit] NULL,
	[PDF] [smallint] NULL,
	[Ativa] [bit] NULL,
	[ContrProt] [bit] NULL,
	[CodGProt] [int] NULL,
	[GrupoPortal] [varchar](80) NULL,
	[CodAux] [varchar](50) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ContasRecorrentes]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ContasRecorrentes](
	[ContaRecorrenteId] [int] NOT NULL,
	[Conta] [varchar](80) NULL,
	[Nome] [varchar](100) NOT NULL,
	[Descricao] [varchar](255) NOT NULL,
	[Vencimento] [int] NULL,
	[Valor] [money] NULL,
	[Status] [varchar](50) NULL,
	[TipoVencimento] [varchar](100) NULL,
	[AntecipaVencimento] [int] NULL,
	[DiasDaSemana] [varchar](50) NULL,
	[Parcela] [int] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PreLancamento]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PreLancamento](
	[PreLancamentoID] [int] NOT NULL,
	[ContaRecorrenteID] [int] NOT NULL,
	[DataVencimento] [datetime] NULL,
	[Conta] [varchar](100) NOT NULL,
	[LancamentoID] [int] NULL
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[viw_contas_a_pagar]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   view [dbo].[viw_contas_a_pagar]                                    
 AS                                                                         
SELECT C.ContaRecorrenteId  as id,                                          
      C.Conta,                                                              
      C.Nome,                                                               
      C.Valor,                                                              
      P.DataVencimento as Vencimento,                                       
      datediff(DAY, GETDATE(),P.DataVencimento) as dias,                    
      L.LançaID LancamentoID,                                               
      L.statusPreLancamento,                                                
      P.PreLancamentoID,                                                    
      CT.LOficial as [Livro Caixa],                                         
      CT.LGerencial as [Livro Gerencial],                                   
      CT.LContábil as [Livro Banco],                                        
      CT.LParticular as [Livro Particular],                                 
      CT.LPortal as [Livro Portal],                                         
      CT.L_IRRF as [Livro I.R.]                                             
 FROM PreLancamento P                                                       
 LEFT JOIN ContasRecorrentes C                                              
   ON C.ContaRecorrenteId = P.ContaRecorrenteID                             
 LEFT JOIN Lançamentos L                                                    
   ON L.PreLancamentoId  = P.PreLancamentoID                                
 LEFT JOIN Contas CT                                                        
   ON CT.Nome = C.Conta                                                     
WHERE C.STATUS = 'Ativo'                                                    
  AND ( L.statusPreLancamento is null OR L.statusPreLancamento = 'pre' );   
GO
/****** Object:  View [dbo].[viw_emolumentos]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   view [dbo].[viw_emolumentos] 
as
SELECT L.DataMov,    
       L.ContaLança      Label,   
    L.ValorLança      Valor,  
    L.NumeroAtosLança Quantidade  
  FROM Lançamentos L  
 WHERE L.LOficialLança = 1   
   AND L.TipoLança = 'Recebimento'    
  
UNION  
  
SELECT L.DataMov,    
       'TOTAL'                Label,   
    SUM(L.ValorLança)      Valor,  
    SUM(L.NumeroAtosLança) Quantidade  
  FROM Lançamentos L  
 WHERE L.LOficialLança = 1   
   AND L.TipoLança = 'Recebimento'    
 GROUP BY L.DataMov  
 
 

GO
/****** Object:  Table [dbo].[tipo_entrada_mov_caixa]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tipo_entrada_mov_caixa](
	[label] [varchar](100) NULL,
	[GrupoLanca] [varchar](50) NULL,
	[ContaLanca] [varchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[viw_movimento_caixa_tipo_entrada]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE    view  [dbo].[viw_movimento_caixa_tipo_entrada]
as
  
SELECT DataMov,  
       MAX(t1.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l1
  JOIN tipo_entrada_mov_caixa t1
    ON l1.GrupoLança = t1.GrupoLanca  
   AND l1.Contalança = t1.ContaLanca
 WHERE t1.label = 'Dinheiro'
 GROUP BY DataMov  
       
 
UNION  
  

SELECT DataMov,  
       MAX(t2.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l2
  JOIN tipo_entrada_mov_caixa t2
    ON l2.GrupoLança = t2.GrupoLanca  
   AND l2.Contalança = t2.ContaLanca
 WHERE t2.label = 'Cartão Débito'
 GROUP BY DataMov   
    
 
UNION  
  

SELECT DataMov,  
       MAX(t3.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l3
  JOIN tipo_entrada_mov_caixa t3
    ON l3.GrupoLança = t3.GrupoLanca  
   AND l3.Contalança = t3.ContaLanca
 WHERE t3.label = 'Crédito Bancário'
 GROUP BY DataMov   
    
 UNION  
  
SELECT DataMov,  
       MAX(t4.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l4
  JOIN tipo_entrada_mov_caixa t4
    ON l4.GrupoLança = t4.GrupoLanca  
   AND l4.Contalança = t4.ContaLanca
 WHERE t4.label = 'Boletos Bancarios'
 GROUP BY DataMov   
    
 UNION   

SELECT DataMov,  
       MAX(t4.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l4
  JOIN tipo_entrada_mov_caixa t4
    ON l4.GrupoLança = t4.GrupoLanca  
   AND l4.Contalança = t4.ContaLanca
 WHERE t4.label = 'Cheques'
 GROUP BY DataMov   
   
 
 UNION   

 
SELECT DataMov,  
       MAX(t4.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l4
  JOIN tipo_entrada_mov_caixa t4
    ON l4.GrupoLança = t4.GrupoLanca  
   AND l4.Contalança = t4.ContaLanca
 WHERE t4.label = 'Cheques Cartório'
 GROUP BY DataMov   
  

 UNION  
 
SELECT DataMov,  
       MAX(t4.label)   Label,  
       SUM(ValorLança) Valor  
  FROM Lançamentos l4
  JOIN tipo_entrada_mov_caixa t4
    ON l4.GrupoLança = t4.GrupoLanca  
   AND l4.Contalança = t4.ContaLanca
 WHERE t4.label = 'Devoluções em Cheque'
 GROUP BY DataMov   
 
 
UNION  
     
  
SELECT DataMov,  
       MAX(t4.label)   Label,  
       SUM(  
         CASE WHEN CHARINDEX('SOBRA',ContaLança) > 0 THEN ValorLança ELSE 0 END -  
         CASE WHEN CHARINDEX('FALTA',ContaLança) > 0 THEN ValorLança ELSE 0 END  
       ) Valor  
  FROM Lançamentos l4
  JOIN tipo_entrada_mov_caixa t4
    ON l4.GrupoLança = t4.GrupoLanca  
   AND l4.Contalança = t4.ContaLanca
 WHERE t4.label = 'Diferença de Caixa'
 GROUP BY DataMov  
  
  
 UNION  
  

 SELECT DataMov,  
       'TOTAL' Label, 
       SUM(
         (
           CASE WHEN a.label not in ('Devoluções em Cheque','Diferença de Caixa') THEN ValorLança ELSE 0 END -  
           CASE WHEN a.label = 'Devoluções em Cheque' THEN ValorLança ELSE 0 END    
         )+
         (  
           CASE WHEN a.label = 'Diferença de Caixa' AND CHARINDEX('SOBRA',ContaLança) > 0 THEN ValorLança ELSE 0 END -  
           CASE WHEN a.label = 'Diferença de Caixa' AND CHARINDEX('FALTA',ContaLança) > 0 THEN ValorLança ELSE 0 END  
         )
       )
  FROM tipo_entrada_mov_caixa a
  JOIN Lançamentos b
    ON b.GrupoLança = a.GrupoLanca 
   AND b.ContaLança = a.ContaLanca 
 GROUP BY DataMov;
GO
/****** Object:  View [dbo].[viw_receitas]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   view [dbo].[viw_receitas] 
as
SELECT DataMov  ,
       'Receita Bruta' Label,
       SUM(ValorBrutoLança) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov 
 
 UNION

 SELECT DataMov,
       'Emolumentos' Label,
       SUM(ValorLança) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov 

  UNION

 SELECT DataMov,
       'Estado' Label,
       SUM(ValorEstado) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov 

  UNION

 SELECT DataMov,
       'Secretaria da Fazenda' Label,
       SUM(ValorIPESP) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov 


  UNION

 SELECT DataMov,
       'Registro Civil' Label,
       SUM(ValorCivil) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov 

  UNION

 SELECT DataMov,
       'Tribunal de Justiça' Label,
       SUM(ValorTribunal) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov  

  UNION

 SELECT DataMov,
       'Santa Casa' Label,
       SUM(ValorStaCasa) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov  

  UNION

 SELECT DataMov,
       'Ministério Público' Label,
       SUM(ValorMP) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov 

  UNION

 SELECT DataMov,
       'ISS' Label,
       SUM(ValorISS) Valor
  FROM Lançamentos 
 WHERE [LOficialLança] = 1
   AND TipoLança = 'Recebimento'
  GROUP by DataMov;
  
  
GO
/****** Object:  Table [dbo].[DadosCartorio]    Script Date: 03/06/2025 14:27:29 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DadosCartorio](
	[RespTit] [nvarchar](50) NULL,
	[RespNome] [nvarchar](50) NULL,
	[RespCPF] [nvarchar](15) NULL,
	[CartNome] [nvarchar](100) NULL,
	[CartComarca] [nvarchar](50) NULL,
	[CartEnd] [varchar](80) NULL,
	[CartCid] [nvarchar](50) NULL,
	[CartCEP] [nvarchar](10) NULL,
	[CartBairro] [nvarchar](30) NULL,
	[CartEst] [nvarchar](2) NULL,
	[CartIR] [float] NULL,
	[CartDeduzir] [money] NULL,
	[LOficialNome1] [nvarchar](50) NULL,
	[LOficialNome2] [nvarchar](50) NULL,
	[LOficialSaldoI] [money] NULL,
	[LOficialInicial] [smallint] NULL,
	[LGerencialNome1] [nvarchar](50) NULL,
	[LGerencialNome2] [nvarchar](50) NULL,
	[LGerencialSaldoI] [money] NULL,
	[LGerencialInicial] [smallint] NULL,
	[LDinheiroNome1] [nvarchar](50) NULL,
	[LDinheiroNome2] [nvarchar](50) NULL,
	[LDinheiroSaldoI] [money] NULL,
	[LDinheiroInicial] [smallint] NULL,
	[LParticularNome1] [nvarchar](50) NULL,
	[LParticularNome2] [nvarchar](50) NULL,
	[LParticularSaldoI] [money] NULL,
	[LParticularInicial] [smallint] NULL,
	[LPrévioNome1] [nvarchar](50) NULL,
	[LPrévioNome2] [nvarchar](50) NULL,
	[LPrévioSaldoI] [money] NULL,
	[LPrévioInicial] [smallint] NULL,
	[LOficialMêsSaldoI] [nvarchar](10) NULL,
	[LGerencialMêsSaldoI] [nvarchar](10) NULL,
	[LDinheiroMêsSaldoI] [nvarchar](10) NULL,
	[LParticularMêsSaldoI] [nvarchar](10) NULL,
	[LPrévioMêsSaldoI] [nvarchar](10) NULL,
	[LOficialAnoSaldoI] [smallint] NULL,
	[LGerencialAnoSaldoI] [smallint] NULL,
	[LDinheiroAnoSaldoI] [smallint] NULL,
	[LParticularAnoSaldoI] [smallint] NULL,
	[LPrévioAnoSaldoI] [smallint] NULL,
	[LOficialNovaPágina] [bit] NOT NULL,
	[LGerencialNovaPágina] [bit] NOT NULL,
	[LDinheiroNovaPágina] [bit] NOT NULL,
	[LParticularNovaPágina] [bit] NOT NULL,
	[LPrévioNovaPágina] [bit] NOT NULL,
	[LOficialHistórico] [bit] NOT NULL,
	[LPortalDNome1] [nvarchar](50) NULL,
	[LGerencialHistórico] [bit] NOT NULL,
	[LPortalDNome2] [nvarchar](50) NULL,
	[LDinheiroHistórico] [bit] NOT NULL,
	[LPortalRNome1] [nvarchar](50) NULL,
	[LParticularHistórico] [bit] NOT NULL,
	[LPortalRNome2] [nvarchar](50) NULL,
	[LPrévioHistórico] [bit] NOT NULL,
	[TipoPortal] [smallint] NULL,
	[L_IRRFNome1] [nvarchar](50) NULL,
	[L_IRRFNome2] [nvarchar](50) NULL,
	[L_IRRFSaldoI] [money] NULL,
	[L_IRRFMêsSaldoI] [nvarchar](10) NULL,
	[L_IRRFAnoSaldoI] [smallint] NULL,
	[L_IRRFNovaPágina] [bit] NULL,
	[L_IRRFHistórico] [bit] NULL,
	[L_IRRFInicial] [smallint] NULL,
	[L_IRRFResIR] [bit] NULL,
	[LOficialResIR] [bit] NULL,
	[PaginaResumos] [nvarchar](6) NULL,
	[L_IRRFDedu] [bit] NULL,
	[LOficialDedu] [bit] NULL,
	[ConciDeb] [bit] NULL,
	[ConciCred] [bit] NULL,
	[ConciDepDin] [bit] NULL,
	[ConciChqCancel] [bit] NULL,
	[ChqEmConciData] [bit] NULL,
	[Exclui_PDF_Orig] [bit] NULL,
	[LGerencialZeraSaldo] [bit] NULL,
	[LParticularZeraSaldo] [bit] NULL,
	[ConciChqExtr] [bit] NULL,
	[Edital] [bit] NULL,
	[Intimacao] [bit] NULL,
	[Telegrama] [bit] NULL,
	[TipoCustasPortal] [smallint] NULL,
	[LOficialFormaEmol] [bit] NULL,
	[L_IRRFFormaEmol] [bit] NULL,
	[L_IRRFSomaEmol] [bit] NULL,
	[L_IRRFTextEmol] [varchar](80) NULL,
	[LGerencialFormaEmol] [bit] NULL,
	[L_IRRFSomaEmolTipo] [nvarchar](6) NULL,
	[L_IRRFSomaEmolGrupo] [bit] NULL,
	[L_IRRFSomaEmolImprime] [bit] NULL,
	[L_IRRFTextEmolHist] [varchar](240) NULL,
	[LOficialLNum] [varchar](10) NULL,
	[L_IRRFLNum] [varchar](10) NULL,
	[LOficialFormaEmolDesp] [bit] NULL,
	[L_IRRFFormaEmolDesp] [bit] NULL,
	[LPartFormaEmol] [bit] NULL,
	[LPartFormaEmolDesp] [bit] NULL,
	[CartCNPJ] [varchar](18) NULL,
	[livro_diario_cpf_cnpj] [varchar](12) NULL,
	[livro_caixa_cpf_cnpj] [varchar](12) NULL,
	[L_IRRF_TipoEmol] [int] NULL,
	[ContTit] [varchar](50) NULL,
	[ContNome] [varchar](50) NULL,
	[ContCPF] [varchar](15) NULL,
	[ContCRC] [varchar](20) NULL,
	[LOficial_ResAssina] [bit] NULL,
	[L_IRRF_ResAssina] [bit] NULL,
	[DataHoraPortal] [bit] NULL,
	[livro_gerenc_cpf_cnpj] [varchar](12) NULL,
	[LOficialLimPag] [int] NULL,
	[LOficialFrenteVerso] [bit] NULL,
	[LOficialPagLayout] [varchar](5) NULL,
	[L_IRRFLimPag] [int] NULL,
	[L_IRRFFrenteVerso] [bit] NULL,
	[L_IRRFPagLayout] [varchar](5) NULL,
	[LGerencialFrenteVerso] [bit] NULL,
	[LGerencialPagLayout] [varchar](5) NULL,
	[GifVago] [bit] NULL,
	[GifCns] [varchar](50) NULL,
	[GifUrlToken] [varchar](100) NULL,
	[GifClientId] [varchar](50) NULL,
	[GifClientSecret] [varchar](50) NULL,
	[GifScope] [varchar](50) NULL,
	[GifDataInicio] [datetime] NULL,
	[GifUrlEnvio] [varchar](100) NULL,
	[GifTokenDeHomologacao] [varchar](100) NULL
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[view_registros]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE   view [dbo].[view_registros]                               
 AS                                                                
SELECT L.LançaID,                                                  
       L.ContaLança,                                               
       L.GrupoLança,                                               
       L.HistLança,                                                
       L.DataMov,                                                  
       ISNULL(L.ValorLança, 0) AS ValorLança,                      
       ISNULL(L.PdfComp, '') AS PdfComp,                           
       ISNULL(C.CodAux, '') AS CodAux,                             
       ISNULL(L.StatusEnvio, 0) AS StatusEnvio,                    
       L.DataEnvio,                                                
       L.ProtocoloEnvio,                                           
       L.ObservacoesEnvio,                                         
          CASE ISNULL(L.StatusEnvio, 0)                            
              WHEN 0 THEN 'Não enviado'                            
              WHEN 1 THEN 'Válido'                                 
              WHEN 2 THEN 'Inválido'                               
              WHEN 3 THEN 'Enviado'                                
              WHEN 4 THEN 'Erro ao Enviar'                         
              Else ''                                              
          END                           AS StatusEnvioNome,        
       GifVago,                                                    
       GifCns,                                                     
       GifCpfPreposto,                                             
       GifUrlToken,                                                
       GifClientId,                                                
       GifClientSecret,                                            
       GifScope,                                                   
       GifUrlEnvio,                                                
       GifDataInicio,                                              
       GifTokenDeHomologacao                                       
 FROM Lançamentos L                                                
 LEFT JOIN Contas C                                                
   ON L.ContaLança = C.Nome                                        
 CROSS APPLY (SELECT                                               
       ISNULL(GifVago, '')                 AS GifVago,             
       ISNULL(GifCns, '')                  AS GifCns,              
       ISNULL(RespCPF, '')                 AS GifCpfPreposto,      
       ISNULL(GifUrlToken, '')             AS GifUrlToken,         
       ISNULL(GifClientId, '')             AS GifClientId,         
       ISNULL(GifClientSecret, '')         AS GifClientSecret,     
       ISNULL(GifScope, '')                AS GifScope,            
       ISNULL(GifUrlEnvio, '')             AS GifUrlEnvio,         
       ISNULL(GifDataInicio, '1753-01-01') AS GifDataInicio,       
       ISNULL(GifTokenDeHomologacao, '') AS GifTokenDeHomologacao  
 FROM  DadosCartorio) DC                                           
 WHERE DataMov > GifDataInicio                                     
       AND TipoLança = 'Pagamento'                                 
       AND LOficialLança = 1                                       
GO
/****** Object:  View [dbo].[viw_resumo_diario]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   view [dbo].[viw_resumo_diario] 
as

SELECT DataMov ,
       'Emolumentos' Label,
       SUM(ValorLança) Valor
  FROM Lançamentos 
 WHERE LOficialLança = 1
   AND TipoLança = 'Recebimento'
 GROUP BY DataMov 

 UNION 

SELECT DataMov ,
       'Despesas' Label,
       SUM(ValorLança) Valor
  FROM Lançamentos 
 WHERE LOficialLança  =1
  and TipoLança = 'Pagamento'
GROUP BY DataMov
 
 UNION

SELECT DataMov ,
       'Resultado Bruto' Label,
       SUM(case when TipoLança  = 'Recebimento' then ValorLança else 0 end -
		   case when TipoLança  = 'Pagamento' then ValorLança else 0 end )    Valor
  FROM Lançamentos 
 WHERE LOficialLança  =1
   AND TipoLança  in ('Pagamento','Recebimento')
 GROUP by DataMov  

 UNION

SELECT DataMov ,
       'BaseCalculoIR' Label,
       SUM(case when TipoLança  = 'Recebimento' then ValorLança else 0 end -
		   case when TipoLança  = 'Pagamento' then ValorLança else 0 end )    Valor
  FROM Lançamentos 
 WHERE L_IRRFLança = 1
   AND TipoLança in ('Pagamento','Recebimento')
 GROUP BY DataMov;
GO
/****** Object:  Table [dbo].[Usuário]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Usuário](
	[Usuário] [nvarchar](20) NULL,
	[PapelTamanho] [nvarchar](2) NULL,
	[SGFPrinter] [nvarchar](50) NULL,
	[Senha] [nvarchar](20) NULL,
	[CamposRelCDT] [nvarchar](120) NULL,
	[email] [varchar](100) NULL,
	[VersaoBase] [varchar](8) NULL,
	[Privilégios] [varchar](30) NULL
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[View_Users]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   VIEW [dbo].[View_Users]
AS
SELECT        Usuário AS [user], Senha AS password
FROM            dbo.Usuário;



GO
/****** Object:  Table [dbo].[Assist_Extrato]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Assist_Extrato](
	[CCNum] [nvarchar](50) NULL,
	[Chave] [nvarchar](11) NULL,
	[LinCol] [nvarchar](5) NULL,
	[Descr] [nvarchar](80) NULL,
	[Valor] [money] NULL,
	[Status] [nvarchar](2) NULL,
	[AutoID] [int] NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Assist_Gestor]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Assist_Gestor](
	[CCNum] [nvarchar](50) NULL,
	[Chave] [nvarchar](11) NULL,
	[LançaID] [int] NULL,
	[AutoID] [int] NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Assist_Grid]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Assist_Grid](
	[CCNum] [nvarchar](50) NULL,
	[Chave] [nvarchar](11) NULL,
	[OrderID] [int] NULL,
	[AutoID] [int] NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[AssistDetalhe]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AssistDetalhe](
	[CCNum] [nvarchar](50) NULL,
	[DataExtr] [datetime] NULL,
	[ValorExtr] [money] NULL,
	[Status] [nvarchar](2) NULL,
	[Docto] [nvarchar](50) NULL,
	[DescrGrid] [nvarchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[AssistItens]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AssistItens](
	[LancaID] [int] NULL,
	[NomeConta] [varchar](80) NULL,
	[Valor] [money] NULL,
	[DataMov] [datetime] NULL,
	[HistLança] [nvarchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[AssistResumo]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AssistResumo](
	[CCNum] [nvarchar](50) NULL,
	[Status] [nvarchar](10) NULL,
	[DataExtr] [datetime] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[atualiza_redis_dash]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[atualiza_redis_dash](
	[nome_tabela] [nvarchar](20) NULL,
	[data] [datetime] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Bancos]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Bancos](
	[CCNum] [nvarchar](50) NULL,
	[BcoNum] [nvarchar](10) NULL,
	[BcoNome] [nvarchar](50) NULL,
	[AgNum] [nvarchar](10) NULL,
	[AgNome] [nvarchar](50) NULL,
	[SaldoInicial] [money] NULL,
	[GerenteResp] [nvarchar](50) NULL,
	[BcoEnd] [nvarchar](50) NULL,
	[BcoBairro] [nvarchar](50) NULL,
	[BcoCEP] [nvarchar](50) NULL,
	[BcoCid] [nvarchar](50) NULL,
	[BcoEstado] [nvarchar](10) NULL,
	[BcoFone] [nvarchar](50) NULL,
	[BcoFax] [nvarchar](50) NULL,
	[BcoEmail] [nvarchar](50) NULL,
	[FolhaInicial] [smallint] NULL,
	[MêsSaldoI] [nvarchar](10) NULL,
	[AnoSaldoI] [smallint] NULL,
	[NovaPágina] [bit] NOT NULL,
	[ApenasHistórico] [bit] NOT NULL,
	[Fechamento] [bit] NULL,
	[Encerrado] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Card]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Card](
	[id] [numeric](18, 0) NOT NULL,
	[titulo] [varchar](50) NULL,
	[descricao] [varchar](1000) NULL,
	[fonte_dados] [varchar](50) NULL,
	[tipo_grafico] [varchar](20) NULL,
	[mostra_grafico] [bit] NULL,
	[mostra_tabela] [bit] NULL,
	[ativo] [bit] NULL,
	[tipo_fonte_dados] [varchar](3) NULL,
	[possui_quantidade] [bit] NULL,
	[formato] [varchar](50) NULL,
	[cor_unica] [bit] NULL,
	[mostra_data_labels] [bit] NULL,
	[possui_percentual] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CardV2]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CardV2](
	[id] [numeric](18, 0) NOT NULL,
	[titulo] [varchar](50) NULL,
	[descricao] [varchar](1000) NULL,
	[fonte_dados] [varchar](50) NULL,
	[tipo_grafico] [varchar](20) NULL,
	[mostra_grafico] [bit] NULL,
	[mostra_tabela] [bit] NULL,
	[ativo] [bit] NULL,
	[tipo_fonte_dados] [varchar](3) NULL,
	[possui_quantidade] [bit] NULL,
	[formato] [varchar](50) NULL,
	[cor_unica] [bit] NULL,
	[mostra_data_labels] [bit] NULL,
	[possui_percentual] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CDT]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CDT](
	[Fatura] [int] NULL,
	[DataVenc] [datetime] NULL,
	[Talao] [int] NULL,
	[DataRegistro] [datetime] NULL,
	[Protocolo] [int] NULL,
	[Parte] [nvarchar](200) NULL,
	[ValorPago] [money] NULL,
	[Recebido] [bit] NULL,
	[DataRecebido] [datetime] NULL,
	[ValorRecebido] [money] NULL,
	[ValorReembolso] [money] NULL,
	[ChaveRecebido] [nvarchar](18) NULL,
	[RegId] [int] NOT NULL,
	[Faturado] [bit] NULL,
	[id_Sist] [int] NULL,
	[id_Recibo] [int] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CDT_Rel]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CDT_Rel](
	[Fatura] [int] NULL,
	[DataVenc] [datetime] NULL,
	[Talao] [int] NULL,
	[DataRegistro] [datetime] NULL,
	[Protocolo] [int] NULL,
	[Parte] [nvarchar](200) NULL,
	[ValorPago] [money] NULL,
	[Recebido] [bit] NULL,
	[DataRecebido] [datetime] NULL,
	[ValorRecebido] [money] NULL,
	[ValorReembolso] [money] NULL,
	[ChaveRecebido] [nvarchar](18) NULL,
	[RegId] [int] NULL,
	[Faturado] [bit] NULL,
	[id_Sist] [int] NULL,
	[id_Recibo] [int] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CDT_RelLista]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CDT_RelLista](
	[Indice] [int] NULL,
	[Texto] [nvarchar](340) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CDT_Temp]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CDT_Temp](
	[Fatura] [int] NULL,
	[DataVenc] [datetime] NULL,
	[Talao] [int] NULL,
	[DataRegistro] [datetime] NULL,
	[Protocolo] [int] NULL,
	[Parte] [nvarchar](200) NULL,
	[ValorPago] [money] NULL,
	[Recebido] [bit] NULL,
	[DataRecebido] [datetime] NULL,
	[ValorRecebido] [money] NULL,
	[ValorReembolso] [money] NULL,
	[ChaveRecebido] [nvarchar](18) NULL,
	[RegId] [int] NULL,
	[Faturado] [bit] NULL,
	[id_Sist] [int] NULL,
	[id_Recibo] [int] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CentrosdeCusto]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CentrosdeCusto](
	[NomeCC] [nvarchar](50) NULL,
	[TipoCC] [nvarchar](10) NULL,
	[CodCC] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ChequesContasRecorrentes]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ChequesContasRecorrentes](
	[ChequeId] [int] NOT NULL,
	[ContaRecorrenteId] [int] NOT NULL,
	[Conta] [varchar](100) NOT NULL,
	[BcoNome] [varchar](100) NOT NULL,
	[Numero] [varchar](8) NOT NULL,
	[Data] [datetime] NOT NULL,
	[Valor] [money] NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ChequesTesouraria]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ChequesTesouraria](
	[Valor] [money] NULL,
	[Mês] [nvarchar](10) NULL,
	[Ano] [smallint] NULL,
	[Obs] [nvarchar](max) NULL,
	[DataChq] [datetime] NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConciBanco]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConciBanco](
	[DataMov] [datetime] NULL,
	[DataLança] [datetime] NULL,
	[ContaLança] [varchar](80) NULL,
	[GrupoLança] [varchar](80) NULL,
	[TipoLança] [nvarchar](30) NULL,
	[FormaLança] [nvarchar](20) NULL,
	[LOficialLança] [bit] NULL,
	[LGerencialLança] [bit] NULL,
	[LBancoLança] [bit] NULL,
	[ValorLança] [money] NULL,
	[CCNumLança] [nvarchar](15) NULL,
	[BcoNomeLança] [nvarchar](30) NULL,
	[ChqLança] [int] NULL,
	[ValorDébito] [money] NULL,
	[ValorCrédito] [money] NULL,
	[Saldo] [money] NULL,
	[LançaID] [int] NULL,
	[LDinheiroLança] [bit] NULL,
	[LParticularLança] [bit] NULL,
	[LPrévioLança] [smallint] NULL,
	[Conciliado] [nvarchar](1) NULL,
	[LPortalLança] [bit] NULL,
	[GrupoPortalLança] [varchar](80) NULL,
	[NumeroAtosLança] [smallint] NULL,
	[ValorBrutoLança] [money] NULL,
	[ValorEstado] [money] NULL,
	[ValorIPESP] [money] NULL,
	[ValorCivil] [money] NULL,
	[ValorTribunal] [money] NULL,
	[ValorStaCasa] [money] NULL,
	[UserLança] [nvarchar](20) NULL,
	[L_IRRFLança] [bit] NULL,
	[DataConci] [datetime] NULL,
	[HistLança] [nvarchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConciExtrato]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConciExtrato](
	[Data] [datetime] NULL,
	[Historico] [nvarchar](50) NULL,
	[Valor] [money] NULL,
	[CredDeb] [nvarchar](7) NULL,
	[CCNum] [nvarchar](15) NULL,
	[OrderID] [int] IDENTITY(1,1) NOT NULL,
	[DataExcl] [datetime] NULL,
	[flag_data] [datetime] NULL,
	[flag_tipo] [nvarchar](1) NULL,
PRIMARY KEY CLUSTERED 
(
	[OrderID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConciMoney]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConciMoney](
	[Histórico] [varchar](50) NULL,
	[Valor] [money] NULL,
	[OrderID] [int] IDENTITY(1,1) NOT NULL,
	[Data] [datetime] NULL,
PRIMARY KEY CLUSTERED 
(
	[OrderID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConfigControleProtocolo]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConfigControleProtocolo](
	[CodGProt] [int] IDENTITY(1,1) NOT NULL,
	[NomeGProt] [varchar](50) NOT NULL,
	[TipoProt] [varchar](1) NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConsContas]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConsContas](
	[Nome] [varchar](80) NULL,
	[GrupoContábil] [varchar](80) NULL,
	[Histórico] [varchar](max) NULL,
	[Tipo de Conta] [nvarchar](25) NULL,
	[Forma de Transação] [nvarchar](20) NULL,
	[LOficial] [bit] NOT NULL,
	[LGerencial] [bit] NOT NULL,
	[LContábil] [bit] NOT NULL,
	[LDinheiro] [bit] NOT NULL,
	[LParticular] [bit] NOT NULL,
	[LPrévio] [smallint] NULL,
	[LPortal] [bit] NOT NULL,
	[L_IRRF] [bit] NULL,
	[GrupoPortal] [varchar](80) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConsLança]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConsLança](
	[DataMov] [datetime] NULL,
	[DataLança] [datetime] NULL,
	[ContaLança] [varchar](80) NULL,
	[GrupoLança] [varchar](80) NULL,
	[TipoLança] [nvarchar](30) NULL,
	[FormaLança] [nvarchar](20) NULL,
	[LOficialLança] [bit] NULL,
	[LGerencialLança] [bit] NULL,
	[LBancoLança] [bit] NULL,
	[ValorLança] [money] NULL,
	[CCNumLança] [nvarchar](15) NULL,
	[BcoNomeLança] [nvarchar](30) NULL,
	[ChqLança] [nvarchar](15) NULL,
	[ValorDébito] [money] NULL,
	[ValorCrédito] [money] NULL,
	[LançaID] [int] NULL,
	[LDinheiroLança] [bit] NULL,
	[LParticularLança] [bit] NULL,
	[LPrévioLança] [smallint] NULL,
	[Conciliado] [nvarchar](1) NULL,
	[LPortalLança] [bit] NULL,
	[NumeroAtosLança] [smallint] NULL,
	[ValorBrutoLança] [money] NULL,
	[ValorEstado] [money] NULL,
	[ValorIPESP] [money] NULL,
	[ValorCivil] [money] NULL,
	[ValorTribunal] [money] NULL,
	[HistLança] [varchar](max) NULL,
	[ValorStaCasa] [money] NULL,
	[UserLança] [nvarchar](20) NULL,
	[L_IRRFLança] [bit] NULL,
	[ValorISS] [money] NULL,
	[ValorMP] [money] NULL,
	[PdfNF] [nvarchar](50) NULL,
	[PdfComp] [nvarchar](50) NULL,
	[DataConci] [datetime] NULL,
	[GrupoPortalLança] [varchar](80) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConsProtocolo]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConsProtocolo](
	[ProtNumero] [varchar](50) NOT NULL,
	[DataMenor] [datetime] NOT NULL,
	[DataMaior] [datetime] NOT NULL,
	[Saldo] [money] NOT NULL,
	[Status] [varchar](10) NOT NULL,
	[Dias] [int] NOT NULL,
	[NomeGProt] [varchar](80) NULL,
	[DataMov] [datetime] NULL,
	[ContaLanca] [varchar](80) NULL,
	[ValorLanca] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ContasProt]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ContasProt](
	[ContasProtId] [int] IDENTITY(1,1) NOT NULL,
	[NomeConta] [varchar](80) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Contratos]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Contratos](
	[ContratoId] [int] NOT NULL,
	[ContaRecorrenteId] [int] NOT NULL,
	[Numero] [varchar](20) NOT NULL,
	[Descricao] [varchar](100) NOT NULL,
	[Fornecedor] [varchar](50) NOT NULL,
	[Contato] [varchar](200) NOT NULL,
	[ValorTotal] [money] NOT NULL,
	[InicioVigencia] [datetime] NOT NULL,
	[FimVigencia] [datetime] NOT NULL,
	[PDF] [varchar](200) NOT NULL,
	[PDFPath] [varchar](200) NULL,
	[Indicador] [varchar](100) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ControleProtocolo]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ControleProtocolo](
	[ProtNumero] [varchar](50) NOT NULL,
	[CodGProt] [int] NOT NULL,
	[Data] [datetime] NOT NULL,
	[Valor] [money] NOT NULL,
	[LançaID] [int] NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[CustasRelCaixaIR]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[CustasRelCaixaIR](
	[Grupo] [varchar](80) NULL,
	[ContaEstado] [varchar](80) NULL,
	[ContaSeFaz] [varchar](80) NULL,
	[ContaStaCasa] [varchar](80) NULL,
	[ContaSinoReg] [varchar](80) NULL,
	[ContaTribunal] [varchar](80) NULL,
	[ContaMP] [varchar](80) NULL,
	[ContaISS] [varchar](80) NULL,
	[HistEstado] [varchar](max) NULL,
	[HistSeFaz] [varchar](max) NULL,
	[HistStaCasa] [varchar](max) NULL,
	[HistSinoReg] [varchar](max) NULL,
	[HistTribunal] [varchar](max) NULL,
	[HistMP] [varchar](max) NULL,
	[HistISS] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DadosIR]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DadosIR](
	[Ano] [nvarchar](4) NULL,
	[Mês] [nvarchar](9) NULL,
	[AnoMês] [nvarchar](6) NULL,
	[MêsNum] [smallint] NULL,
	[ValorP] [float] NULL,
	[ValorRS] [money] NULL,
	[Lista] [nvarchar](30) NULL,
	[MaxFaixa] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DatabaseVersion]    Script Date: 03/06/2025 14:27:30 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DatabaseVersion](
	[Version] [varchar](15) NULL,
	[IsUpdating] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Deducoes]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Deducoes](
	[Tipo] [nvarchar](20) NULL,
	[Ano] [nvarchar](4) NULL,
	[Mês] [nvarchar](9) NULL,
	[AnoMês] [nvarchar](6) NULL,
	[MêsNum] [smallint] NULL,
	[Descrição] [nvarchar](60) NULL,
	[Valor] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DeduHist]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DeduHist](
	[Tipo] [nvarchar](20) NULL,
	[Ano] [nvarchar](4) NULL,
	[Mês] [nvarchar](9) NULL,
	[AnoMês] [nvarchar](6) NULL,
	[MêsNum] [smallint] NULL,
	[Descrição] [nvarchar](60) NULL,
	[Valor] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DepósitoPrévio]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DepósitoPrévio](
	[Tipo] [nvarchar](25) NULL,
	[Valor] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[EspExtrato]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[EspExtrato](
	[Tipo] [nvarchar](20) NULL,
	[NomeExtrato] [nvarchar](100) NULL,
	[CCNum] [nvarchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[EspGestor]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[EspGestor](
	[Tipo] [nvarchar](20) NULL,
	[NomeConta] [varchar](80) NULL,
	[CCNum] [nvarchar](50) NULL,
	[TipoConta] [nvarchar](25) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Flags]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Flags](
	[CampoI] [nvarchar](10) NULL,
	[CampoV] [nvarchar](20) NULL,
	[CampoU] [nvarchar](12) NULL,
	[CampoB] [nvarchar](10) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[GrupoContábil]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[GrupoContábil](
	[Nome] [varchar](80) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[GrupoPortal]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[GrupoPortal](
	[CodGrupoPortal] [smallint] NULL,
	[TipoGrupo] [real] NULL,
	[NomeGrupo] [varchar](80) NULL,
	[UF] [varchar](2) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[IntensEspTemp]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[IntensEspTemp](
	[LancaID] [nvarchar](max) NULL,
	[Valor] [money] NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceArq]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceArq](
	[NomeTipo] [nvarchar](50) NULL,
	[Extensão] [nvarchar](5) NULL,
	[FormaColunas] [nvarchar](15) NULL,
	[LocalArquivos] [nvarchar](200) NULL,
	[Linha1] [smallint] NULL,
	[LinhaF] [smallint] NULL,
	[LimpaCol] [bit] NULL,
	[Cab_Ult_Col] [smallint] NULL,
	[Cab_Ult_Text] [nvarchar](20) NULL,
	[Rod_Pri_Col] [smallint] NULL,
	[Rod_Pri_Text] [nvarchar](20) NULL,
	[InterfaceInicial] [bit] NULL,
	[Cab_Ult_Oco] [smallint] NULL,
	[Rod_Pri_Oco] [smallint] NULL,
	[InterfaceEntrManual] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceCheque]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceCheque](
	[ContaSGF] [varchar](80) NULL,
	[Precedente1] [nvarchar](50) NULL,
	[Historico1] [nvarchar](50) NULL,
	[Precedente2] [nvarchar](50) NULL,
	[Historico2] [nvarchar](50) NULL,
	[Precedente3] [nvarchar](50) NULL,
	[Historico3] [nvarchar](50) NULL,
	[Precedente4] [nvarchar](50) NULL,
	[Historico4] [nvarchar](50) NULL,
	[Cidade] [nvarchar](50) NULL,
	[Data] [bit] NOT NULL,
	[AnoDigitos] [bit] NOT NULL,
	[Cruzar] [bit] NOT NULL,
	[Verso] [bit] NOT NULL,
	[LayoutAuto] [bit] NOT NULL,
	[Verso1] [nvarchar](50) NULL,
	[Verso2] [nvarchar](50) NULL,
	[VersoCampo1] [nvarchar](20) NULL,
	[VersoCampo2] [nvarchar](20) NULL,
	[ImprimeCopias] [bit] NOT NULL,
	[NCopias] [nvarchar](1) NULL,
	[ChqMaxValor] [bit] NULL,
	[ValorMaxChq] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceComum]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceComum](
	[LocalCodigo] [nvarchar](50) NULL,
	[LocalDataMovimento] [nvarchar](50) NULL,
	[LocalValor] [nvarchar](50) NULL,
	[LocalForma] [nvarchar](50) NULL,
	[LocalAtos] [nvarchar](50) NULL,
	[LocalVlBruto] [nvarchar](50) NULL,
	[LocalEstado] [nvarchar](50) NULL,
	[LocalIPESP] [nvarchar](50) NULL,
	[LocalStaCasa] [nvarchar](50) NULL,
	[LocalRegCivil] [nvarchar](50) NULL,
	[LocalTribunal] [nvarchar](50) NULL,
	[TipoArq] [nvarchar](50) NULL,
	[LocalISS] [nvarchar](50) NULL,
	[LocalMP] [nvarchar](50) NULL,
	[LocalEdital] [nvarchar](50) NULL,
	[LocalIntimacao] [nvarchar](50) NULL,
	[LocalTelegrama] [nvarchar](50) NULL,
	[LocalProtocolo] [varchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceContas]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceContas](
	[ContaOrigem] [nvarchar](50) NULL,
	[ContaSGF] [varchar](80) NULL,
	[ContaInterID] [int] NULL,
	[TipoArq] [nvarchar](50) NULL,
	[CodCC] [nvarchar](4) NULL,
	[CodUN] [nvarchar](4) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceDataArq]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceDataArq](
	[NomeArq] [nvarchar](50) NULL,
	[Usuario] [nvarchar](50) NULL,
	[DataArq] [datetime] NULL,
	[HoraArq] [datetime] NULL,
	[LinhasArq] [smallint] NULL,
	[TipoArq] [nvarchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceExtrato]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceExtrato](
	[CCNum] [nvarchar](15) NULL,
	[BcoNome] [nvarchar](30) NULL,
	[LinCab] [smallint] NULL,
	[ColData] [smallint] NULL,
	[ColDescr] [smallint] NULL,
	[ColChqNum] [smallint] NULL,
	[ColCred] [smallint] NULL,
	[ColDeb] [smallint] NULL,
	[Auto1Conc] [bit] NULL,
	[DiasBusca] [nvarchar](2) NULL,
	[Grid_1pV] [bit] NULL,
	[Grid_Vp1] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceExtratoComp]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceExtratoComp](
	[CCNum] [nvarchar](15) NULL,
	[BcoNome] [nvarchar](30) NULL,
	[Descr] [varchar](80) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceExtratoGrid]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceExtratoGrid](
	[CCNum] [nvarchar](15) NULL,
	[BcoNome] [nvarchar](30) NULL,
	[Descr] [nvarchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceExtratoTarifa]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceExtratoTarifa](
	[CCNum] [nvarchar](15) NULL,
	[BcoNome] [nvarchar](30) NULL,
	[Descr] [nvarchar](50) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceFormaPgto]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceFormaPgto](
	[FormaID] [int] NULL,
	[FormaSist] [nvarchar](50) NULL,
	[FormaSGF] [nvarchar](50) NULL,
	[BcoSGF] [nvarchar](50) NULL,
	[CCNumSGF] [nvarchar](50) NULL,
	[TipoArq] [nvarchar](50) NULL,
	[ChequeSGF] [nvarchar](15) NULL,
	[ChequeSGFIni] [smallint] NULL,
	[ChequeSGFTam] [smallint] NULL,
	[ChequeSGFFim] [smallint] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InterfaceHistorico]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InterfaceHistorico](
	[ContaOrigem] [nvarchar](50) NULL,
	[Precedente1] [nvarchar](50) NULL,
	[Historico1] [nvarchar](50) NULL,
	[Precedente2] [nvarchar](50) NULL,
	[Historico2] [nvarchar](50) NULL,
	[Precedente3] [nvarchar](50) NULL,
	[Historico3] [nvarchar](50) NULL,
	[Precedente4] [nvarchar](50) NULL,
	[Historico4] [nvarchar](50) NULL,
	[Precedente5] [nvarchar](50) NULL,
	[Historico5] [nvarchar](50) NULL,
	[Precedente6] [nvarchar](50) NULL,
	[Historico6] [nvarchar](50) NULL,
	[Precedente7] [nvarchar](50) NULL,
	[Historico7] [nvarchar](50) NULL,
	[Precedente8] [nvarchar](50) NULL,
	[Historico8] [nvarchar](50) NULL,
	[TipoArq] [nvarchar](50) NULL,
	[HistIni1] [smallint] NULL,
	[HistTam1] [smallint] NULL,
	[HistFim1] [smallint] NULL,
	[HistIni2] [smallint] NULL,
	[HistTam2] [smallint] NULL,
	[HistFim2] [smallint] NULL,
	[HistIni3] [smallint] NULL,
	[HistTam3] [smallint] NULL,
	[HistFim3] [smallint] NULL,
	[HistIni4] [smallint] NULL,
	[HistTam4] [smallint] NULL,
	[HistFim4] [smallint] NULL,
	[HistIni5] [smallint] NULL,
	[HistTam5] [smallint] NULL,
	[HistFim5] [smallint] NULL,
	[HistIni6] [smallint] NULL,
	[HistTam6] [smallint] NULL,
	[HistFim6] [smallint] NULL,
	[HistIni7] [smallint] NULL,
	[HistTam7] [smallint] NULL,
	[HistFim7] [smallint] NULL,
	[HistIni8] [smallint] NULL,
	[HistTam8] [smallint] NULL,
	[HistFim8] [smallint] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Lanca_exclui]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Lanca_exclui](
	[DataMov] [datetime] NULL,
	[DataLança] [datetime] NULL,
	[ContaLança] [varchar](80) NULL,
	[GrupoLança] [varchar](80) NULL,
	[TipoLança] [nvarchar](30) NULL,
	[FormaLança] [nvarchar](20) NULL,
	[LOficialLança] [bit] NULL,
	[LGerencialLança] [bit] NULL,
	[LBancoLança] [bit] NULL,
	[ValorLança] [money] NULL,
	[CCNumLança] [nvarchar](15) NULL,
	[BcoNomeLança] [nvarchar](30) NULL,
	[ChqLança] [nvarchar](15) NULL,
	[ValorDébito] [money] NULL,
	[ValorCrédito] [money] NULL,
	[LançaID] [int] NOT NULL,
	[LDinheiroLança] [bit] NULL,
	[LParticularLança] [bit] NULL,
	[LPrévioLança] [smallint] NULL,
	[Conciliado] [nvarchar](1) NULL,
	[LPortalLança] [bit] NULL,
	[NumeroAtosLança] [smallint] NULL,
	[ValorBrutoLança] [money] NULL,
	[ValorEstado] [money] NULL,
	[ValorIPESP] [money] NULL,
	[ValorCivil] [money] NULL,
	[ValorTribunal] [money] NULL,
	[ValorStaCasa] [money] NULL,
	[HistLança] [varchar](max) NULL,
	[UserLança] [nvarchar](20) NULL,
	[L_IRRFLança] [bit] NULL,
	[ValorISS] [money] NULL,
	[ValorMP] [money] NULL,
	[PdfNF] [nvarchar](50) NULL,
	[PdfComp] [nvarchar](50) NULL,
	[DataConci] [datetime] NULL,
	[ValorEdital] [money] NULL,
	[ValorIntimacao] [money] NULL,
	[ValorTelegrama] [money] NULL,
	[flag_data] [datetime] NULL,
	[flag_tipo] [nvarchar](1) NULL,
	[ProtNumero] [varchar](50) NULL,
	[GrupoPortalLança] [varchar](80) NULL,
	[DataEnvio] [date] NULL,
	[StatusEnvio] [smallint] NULL,
	[ProtocoloEnvio] [uniqueidentifier] NULL,
	[ObservacoesEnvio] [varchar](200) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[LançaRel]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[LançaRel](
	[DataMov] [datetime] NULL,
	[DataLança] [datetime] NULL,
	[ContaLança] [varchar](80) NULL,
	[GrupoLança] [varchar](80) NULL,
	[TipoLança] [nvarchar](30) NULL,
	[FormaLança] [nvarchar](20) NULL,
	[LOficialLança] [bit] NULL,
	[LGerencialLança] [bit] NULL,
	[LBancoLança] [bit] NULL,
	[ValorLança] [money] NULL,
	[CCNumLança] [nvarchar](15) NULL,
	[BcoNomeLança] [nvarchar](30) NULL,
	[ChqLança] [int] NULL,
	[ValorDébito] [money] NULL,
	[ValorCrédito] [money] NULL,
	[Saldo] [money] NULL,
	[LDinheiroLança] [bit] NULL,
	[LParticularLança] [bit] NULL,
	[LPrévioLança] [smallint] NULL,
	[Conciliado] [nvarchar](1) NULL,
	[LançaID] [int] NULL,
	[LPortalLança] [bit] NULL,
	[NumeroAtosLança] [int] NULL,
	[ValorBrutoLança] [money] NULL,
	[ValorEstado] [money] NULL,
	[ValorIPESP] [money] NULL,
	[ValorCivil] [money] NULL,
	[ValorTribunal] [money] NULL,
	[HistLança] [varchar](max) NULL,
	[ValorStaCasa] [money] NULL,
	[UserLança] [nvarchar](20) NULL,
	[L_IRRFLança] [bit] NULL,
	[ValorISS] [money] NULL,
	[ValorMP] [money] NULL,
	[PdfNF] [nvarchar](50) NULL,
	[PdfComp] [nvarchar](50) NULL,
	[DataConci] [datetime] NULL,
	[PercentCC] [float] NULL,
	[NomeCC] [nvarchar](50) NULL,
	[ValorEdital] [money] NULL,
	[ValorIntimacao] [money] NULL,
	[ValorTelegrama] [money] NULL,
	[PercentUN] [float] NULL,
	[NomeUN] [nvarchar](50) NULL,
	[CodCC] [nvarchar](6) NULL,
	[CodUN] [nvarchar](6) NULL,
	[SomaCredito] [money] NULL,
	[SomaDebito] [money] NULL,
	[GrupoPortalLança] [varchar](80) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[log_gestor]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[log_gestor](
	[Id] [int] NOT NULL,
	[datahora] [datetime] NULL,
	[usario] [varchar](20) NOT NULL,
	[descricao] [varchar](500) NOT NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Movimento]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Movimento](
	[Nome] [varchar](80) NULL,
	[Valor] [money] NULL,
	[Cheques] [money] NULL,
	[Creditos] [money] NULL,
	[Debitos] [money] NULL,
	[Disponivel] [money] NULL,
	[Tipo] [nvarchar](8) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RateioCC_Conta]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RateioCC_Conta](
	[ContaNome] [varchar](80) NULL,
	[PercentCC] [float] NULL,
	[CodCC] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RateioCC_Lança]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RateioCC_Lança](
	[LançaID] [int] NULL,
	[PercentCC] [float] NULL,
	[CodCC] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RateioCC_Temp]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RateioCC_Temp](
	[ContaNome] [varchar](80) NULL,
	[PercentCC] [float] NULL,
	[CodCC] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RateioUN_Conta]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RateioUN_Conta](
	[ContaNome] [nvarchar](50) NULL,
	[PercentUN] [float] NULL,
	[CodUN] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RateioUN_Lança]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RateioUN_Lança](
	[LançaID] [int] NULL,
	[PercentUN] [float] NULL,
	[CodUN] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RateioUN_Temp]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RateioUN_Temp](
	[ContaNome] [nvarchar](50) NULL,
	[PercentUN] [float] NULL,
	[CodUN] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Relatório]    Script Date: 03/06/2025 14:27:31 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Relatório](
	[Livro] [nvarchar](25) NULL,
	[Mês] [nvarchar](10) NULL,
	[SaldoInicial] [money] NULL,
	[CCNum] [nvarchar](15) NULL,
	[BcoNome] [nvarchar](50) NULL,
	[FolhaInicial] [smallint] NULL,
	[PapelTamanho] [nvarchar](6) NULL,
	[Ano] [nvarchar](4) NULL,
	[NomeEntrada] [nvarchar](15) NULL,
	[NomeSaida] [nvarchar](15) NULL,
	[NovaPagConcExtr] [bit] NULL,
	[RelUpper] [bit] NULL,
	[FormatoRelAlt] [bit] NULL,
	[LivroNum] [varchar](10) NULL,
	[FormatoRelLivro] [int] NULL,
	[AjusteMargem] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Resumo]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Resumo](
	[Ano] [nvarchar](4) NULL,
	[Mês] [nvarchar](9) NULL,
	[Livro] [nvarchar](35) NULL,
	[SaldoInicial] [money] NULL,
	[SaldoFinal] [money] NULL,
	[PaginaInicial] [smallint] NULL,
	[PaginaFinal] [smallint] NULL,
	[BcoNome] [nvarchar](50) NULL,
	[CCNum] [nvarchar](50) NULL,
	[Entradas] [money] NULL,
	[Saidas] [money] NULL,
	[MêsNum] [smallint] NULL,
	[FormaEmol] [bit] NULL,
	[SomaEmol] [bit] NULL,
	[TextEmol] [varchar](80) NULL,
	[SomaEmolTipo] [nvarchar](6) NULL,
	[SomaEmolGrupo] [bit] NULL,
	[SomaEmolImprime] [bit] NULL,
	[TextEmolHist] [varchar](240) NULL,
	[LivroNum] [varchar](10) NULL,
	[FormaEmolDesp] [bit] NULL,
	[L_IRRF_TipoEmol] [int] NULL,
	[LivroLimPag] [int] NULL,
	[LivroFrenteVerso] [bit] NULL,
	[LivroPagLayout] [varchar](5) NULL,
	[FormatoRelLivro] [int] NULL,
	[LivroCPF_CNPJ] [varchar](12) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[SaldoAtual]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[SaldoAtual](
	[Tipo] [nvarchar](50) NULL,
	[Numero] [nvarchar](50) NULL,
	[SaldoAtual] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[scores]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[scores](
	[id] [numeric](18, 0) NOT NULL,
	[fonte_dados] [varchar](50) NULL,
	[ativo] [bit] NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[tbl_tmp_despesas]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_tmp_despesas](
	[DataMov] [datetime] NULL,
	[label] [varchar](104) NULL,
	[Valor] [numeric](12, 2) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[TempRel]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[TempRel](
	[DataMov] [datetime] NULL,
	[DataLança] [datetime] NULL,
	[ContaLança] [varchar](80) NULL,
	[GrupoLança] [varchar](80) NULL,
	[TipoLança] [nvarchar](30) NULL,
	[FormaLança] [nvarchar](20) NULL,
	[LOficialLança] [bit] NULL,
	[LGerencialLança] [bit] NULL,
	[LBancoLança] [bit] NULL,
	[ValorLança] [money] NULL,
	[CCNumLança] [nvarchar](15) NULL,
	[BcoNomeLança] [nvarchar](30) NULL,
	[ChqLança] [int] NULL,
	[ValorDébito] [money] NULL,
	[ValorCrédito] [money] NULL,
	[Saldo] [money] NULL,
	[LançaID] [int] NULL,
	[LDinheiroLança] [bit] NULL,
	[LParticularLança] [bit] NULL,
	[LPrévioLança] [smallint] NULL,
	[Conciliado] [nvarchar](1) NULL,
	[LPortalLança] [bit] NULL,
	[ValorBrutoLança] [money] NULL,
	[ValorEstado] [money] NULL,
	[ValorIPESP] [money] NULL,
	[ValorCivil] [money] NULL,
	[ValorTribunal] [money] NULL,
	[HistLança] [varchar](max) NULL,
	[ValorStaCasa] [money] NULL,
	[NumeroAtosLança] [int] NULL,
	[UserLança] [nvarchar](20) NULL,
	[L_IRRFLança] [bit] NULL,
	[ValorISS] [money] NULL,
	[ValorMP] [money] NULL,
	[PdfNF] [nvarchar](50) NULL,
	[PdfComp] [nvarchar](50) NULL,
	[DataConci] [datetime] NULL,
	[PercentCC] [float] NULL,
	[NomeCC] [nvarchar](50) NULL,
	[ValorEdital] [money] NULL,
	[ValorIntimacao] [money] NULL,
	[ValorTelegrama] [money] NULL,
	[PercentUN] [float] NULL,
	[NomeUN] [nvarchar](50) NULL,
	[CodCC] [nvarchar](6) NULL,
	[CodUN] [nvarchar](6) NULL,
	[GrupoPortalLança] [varchar](80) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[UnidadeNegocio]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[UnidadeNegocio](
	[NomeUN] [nvarchar](50) NULL,
	[TipoUN] [nvarchar](10) NULL,
	[CodUN] [nvarchar](6) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ValidaMes]    Script Date: 03/06/2025 14:27:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ValidaMes](
	[Tipo] [nvarchar](50) NULL,
	[Numero] [nvarchar](50) NULL,
	[SaldoInicial] [money] NULL
) ON [PRIMARY]
GO
/****** Object:  Index [idx_rateiocclanca_lancaid]    Script Date: 03/06/2025 14:27:32 ******/
CREATE NONCLUSTERED INDEX [idx_rateiocclanca_lancaid] ON [dbo].[RateioCC_Lança]
(
	[LançaID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [idx_rateiounlanca_lancaid]    Script Date: 03/06/2025 14:27:32 ******/
CREATE NONCLUSTERED INDEX [idx_rateiounlanca_lancaid] ON [dbo].[RateioUN_Lança]
(
	[LançaID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[Contas] ADD  DEFAULT ((0)) FOR [ContrProt]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [L_IRRFSomaEmolGrupo]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [L_IRRFSomaEmolImprime]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [LOficialFormaEmolDesp]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [L_IRRFFormaEmolDesp]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [LPartFormaEmol]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [LPartFormaEmolDesp]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [LOficial_ResAssina]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [L_IRRF_ResAssina]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [DataHoraPortal]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [LOficialFrenteVerso]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [L_IRRFFrenteVerso]
GO
ALTER TABLE [dbo].[DadosCartorio] ADD  DEFAULT ((0)) FOR [LGerencialFrenteVerso]
GO
ALTER TABLE [dbo].[Relatório] ADD  DEFAULT ((0)) FOR [FormatoRelAlt]
GO
ALTER TABLE [dbo].[Relatório] ADD  CONSTRAINT [D_Resumo_AjusteMargem]  DEFAULT ((0)) FOR [AjusteMargem]
GO
ALTER TABLE [dbo].[Resumo] ADD  DEFAULT ((0)) FOR [SomaEmolGrupo]
GO
ALTER TABLE [dbo].[Resumo] ADD  DEFAULT ((0)) FOR [SomaEmolImprime]
GO
ALTER TABLE [dbo].[Resumo] ADD  DEFAULT ((0)) FOR [FormaEmolDesp]
GO
ALTER TABLE [dbo].[Resumo] ADD  DEFAULT ((0)) FOR [LivroFrenteVerso]
GO
USE [master]
GO
ALTER DATABASE [$BASE_NOVA] SET  READ_WRITE 
GO
