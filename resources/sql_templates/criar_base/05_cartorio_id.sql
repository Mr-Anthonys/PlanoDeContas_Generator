USE [$BASE_NOVA]
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE  object_id = OBJECT_ID(N'[dbo].[Flags]') AND name = 'Cartorio_id')
BEGIN	
	ALTER TABLE Flags ADD Cartorio_id NVARCHAR(200)	
END
GO

UPDATE Flags SET Cartorio_id = $CART_ID
GO
