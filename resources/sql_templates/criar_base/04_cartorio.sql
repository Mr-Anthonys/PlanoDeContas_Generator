use [$BASE_NOVA]
go

update DadosCartorio set
CartNome = '$CART_NOME'
,GifCns = '$CART_CNS'
,CartCid = '$CART_CIDADE'
,CartEst = '$CART_ESTADO'
,CartEnd = '$CART_ENDERECO'
,CartBairro = '$CART_BAIRRO'
,CartCEP = '$CART_CEP'
,RespNome = '$CART_RESP_NOME'
,RespCPF = '$CART_RESP_CPF'
,GifDataInicio = '$CART_INICIO'
,CartCNPJ = '$CART_CNPJ'
,GifClientId = ''
,GifClientSecret = ''
go
