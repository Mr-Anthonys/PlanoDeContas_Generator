USE Gestor_Parametros
GO

INSERT [dbo].[Parametros_Clientes] ([Nome], [Servidor], [Banco], [Usuario], [Senha], [DiretorioArquivo], [Odbc], [BrowserDashboard], [UrlDashboard], [UrlDashboardToken], [DiretorioMensalistas], [UrlValidacao]) VALUES (
N'$NOME',
N'$HOST', 
N'$BASE_NOVA', 
N'$BASE_USUARIO', 
N'$PASS', 
N'$DIR', 
N'DSN=$ODBC;UID=$BASE_USUARIO;PWD=$PASS;', 
N'CHROME', 
N'https://dashboard-frontend-master.herokuapp.com/',
N'https://dashboard-frontend-master.herokuapp.com/sessions', 
N'C:\ProPackages\Mensalistas\Propackage.Gestor.UI.exe', 
N'')
GO

-- $NOME
-- $HOST
-- $USER
-- $PASS
-- $DIR
-- $ODBC

-- INSERT [dbo].[Parametros_Clientes] ([Nome], [Servidor], [Banco], [Usuario], [Senha], [DiretorioArquivo], [Odbc], [BrowserDashboard], [UrlDashboard], [UrlDashboardToken], [DiretorioMensalistas], [UrlValidacao]) VALUES (
-- N'Gestor_SP_SaoJoaoDaBoaVista_1TNPROT', $NOME
-- N'192.168.10.167',  $HOST
-- N'Gestor_SP_SaoJoaoDaBoaVista_1TNPROT', $NOME
-- N'dba_propackages', $USER
-- N'@wkul?4%jm7qA>p^k!gp', $PASS
-- N'C:\ProPackages\Arquivos\Gestor_SP_SaoJoaoDaBoaVista_1TNPROT\', $DIR
-- N'DSN=ODBC_GF_SP_SaoJoaoDaBoaVis;UID=dba_propackages;PWD=@wkul?4%jm7qA>p^k!gp;', $ODBC
-- N'CHROME', 
-- N'https://dashboard-frontend-master.herokuapp.com/',
-- N'https://dashboard-frontend-master.herokuapp.com/sessions', 
-- N'C:\ProPackages\Mensalistas\Propackage.Gestor.UI.exe', 
-- N'')
-- GO

-- $NOME_DEV
-- $HOST_DEV
-- $USER_DEV
-- $PASS_DEV
-- $DIR_DEV
-- $ODBC

-- INSERT [dbo].[Parametros_Clientes] ([Nome], [Servidor], [Banco], [Usuario], [Senha], [DiretorioArquivo], [Odbc], [BrowserDashboard], [UrlDashboard], [UrlDashboardToken], [DiretorioMensalistas], [UrlValidacao]) VALUES (
-- N'INR - Gestor_PA_Ruropolis',
-- N'18.229.78.5', 
-- N'Gestor_PA_Ruropolis', 
-- N'$USER', 
-- N'$PASS', 
-- N'C:\ProPackages\Clientes\INR\Arquivos\PA RUROLOPIS\', 
-- N'DSN=ODBC_GF_PA_Ruropolis;UID=$USER;PWD=$PASS;', 
-- N'CHROME', 
-- N'https://dashboard-frontend-master.herokuapp.com/',
-- N'https://dashboard-frontend-master.herokuapp.com/sessions', 
-- N'C:\ProPackages\Mensalistas\Propackage.Gestor.UI.exe', 
-- N'')
-- GO

--INSERT [dbo].[Parametros_Clientes] ([Nome], [Servidor], [Banco], [Usuario], [Senha], [DiretorioArquivo], [Odbc], [BrowserDashboard], [UrlDashboard], [UrlDashboardToken], [DiretorioMensalistas], [UrlValidacao]) VALUES (
--N'Heros - Gestor_SP_SaoJoaoDaBoaVista_1TNPROT',
--N'192.168.10.167', 
--N'Gestor_SP_SaoJoaoDaBoaVista_1TNPROT', 
--N'dba_propackages', 
--N'@wkul?4%jm7qA>p^k!gp', 
--N'C:\ProPackages\Clientes\Heros\Arquivos\Gestor_SP_SaoJoaoDaBoaVista_1TNPROT\', 
--N'DSN=ODBC_GF_SP_SaoJoaoDaBoaVis;UID=dba_propackages;PWD=@wkul?4%jm7qA>p^k!gp;', 
--N'CHROME', 
--N'https://dashboard-frontend-master.herokuapp.com/',
--N'https://dashboard-frontend-master.herokuapp.com/sessions', 
--N'C:\ProPackages\Mensalistas\Propackage.Gestor.UI.exe', 
--N'')
--GO
