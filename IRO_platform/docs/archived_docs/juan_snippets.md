# To verify that *tenant_test1* and *tenant_test2* schemas (and their tables) were created successfully by the `01-init-schemas.sql` script, you can connect directly to the PostgreSQL database container and run a few inspection commands. Below are two common ways to do this:

---

## 1) Via `psql` in the DB container

1. **Open a PostgreSQL shell** inside the `db` container:
   ```bash
   docker compose exec db psql -U dma_user -d dma_db
   ```
   This starts an interactive `psql` session as user `dma_user` in database `dma_db`.

2. **List all schemas**:
   ```sql
   \dn
   ```
   You should see both `public`, `tenant_test1`, `tenant_test2`, plus any built-in schemas (e.g., `pg_catalog`).

3. **List tables in your new tenant schemas** (for example, `tenant_test1`):
   ```sql
   \dt tenant_test1.*
   ```
   You should see tables like `iro`, `iro_version`, `iro_relationship`, `impact_assessment`, etc.

4. **Check data inserted into `public.tenant_config`**:
   ```sql
   SELECT * FROM public.tenant_config;
   ```
   You should see rows for `test1` and `test2`.  

5. **(Optional) Query a tenant table directly**:
   ```sql
   SELECT * FROM tenant_test1.iro;
   ```
   This confirms the table exists and is queryable.

6. **Exit** the `psql` shell by typing:
   ```sql
   \q
   ```
