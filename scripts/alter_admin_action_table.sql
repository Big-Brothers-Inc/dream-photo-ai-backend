-- Изменение типа столбца target_id в таблице AdminAction
ALTER TABLE "AdminAction" ALTER COLUMN target_id TYPE BIGINT;

-- Также изменим тип столбца admin_id для согласованности
ALTER TABLE "AdminAction" ALTER COLUMN admin_id TYPE BIGINT;

-- Проверка успешного выполнения
SELECT 
    column_name, 
    data_type 
FROM 
    information_schema.columns 
WHERE 
    table_name = 'AdminAction' AND 
    (column_name = 'target_id' OR column_name = 'admin_id'); 