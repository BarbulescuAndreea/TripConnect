DO $$BEGIN
    IF NOT EXISTS(SELECT 1 FROM pg_database WHERE datname = 'trip_connect') THEN
        CREATE DATABASE trip_connect;
    END IF;
END$$;
