Inspired by https://github.com/jdelic/django-postgresql-setrole

https://github.com/hashicorp/vault/issues/1857#issuecomment-248441989

```python
client.write(
    join(PG_MOUNT, 'config/connection'),
    lease='10s', lease_max='10s',
    connection_url='postgresql://'
                   'vault:azaza'
                   '@trash.force.fm:5432/postgres'
)
client.write(
    join(PG_MOUNT, 'roles', 'db-full-access'),
    sql="""
    CREATE ROLE "{{name}}"
        WITH LOGIN ENCRYPTED PASSWORD '{{password}}'
        VALID UNTIL '{{expiration}}'
        IN ROLE "force_fm" INHERIT NOCREATEROLE NOCREATEDB NOSUPERUSER NOREPLICATION NOBYPASSRLS;
    """,
    revocation_sql="""
    DROP ROLE "{{name}}";
    """
)
```

```python
DATABASES = {
    'default': {
        'NAME': 'force_fm',
        'ENGINE': 'pgvault',
        'HOST': 'trash.force.fm',
        'USER': 'force_fm',  # SET ROLE USER
        'PORT': '',
        'CONN_MAX_AGE': 6000,
        'VAULT': {
            'URL': 'https://trash.force.fm:18400',
            'TOKEN': '',
            'MOUNT': 'force.fm/postgresql',
            'ROLE': 'db-full-access',
            'CERTS': (
                os.path.join(CERTS_DIR, 'client1__bundle.crt'),
                os.path.join(CERTS_DIR, 'client1.key'),
            ),
            'VERIFY': os.path.join(CERTS_DIR, 'force.fm__root_ca.crt'),
        }
    }
}
```

