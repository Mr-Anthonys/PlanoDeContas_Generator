use [$BASE_NOVA]
go

update Contas set L_IRRF = 0 where nome not like '%REMUNERA%'
update Lançamentos set L_IRRFLança = 0 where ContaLança not like '%REMUNERA%'
