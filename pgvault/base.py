import hvac
from os.path import join

from django.db.backends.signals import connection_created
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql.base import DatabaseWrapper as DjangoPostgresqlDatabaseWrapper
from django.dispatch import receiver


REQUIRED_VAULT_OPTIONS = ['URL', 'TOKEN', 'MOUNT', 'ROLE']


class DatabaseWrapper(DjangoPostgresqlDatabaseWrapper):
    def _get_vault_client_connection_options(self) -> dict:
        _vault = self.settings_dict['VAULT']
        opts = {
            'url': _vault['URL'],
            'token': _vault['TOKEN']
        }
        if _vault.get('CERT'):
            opts['cert'] = _vault['CERT']
        if _vault.get('VERIFY'):
            opts['verify'] = _vault['VERIFY']
        return opts

    def _get_vault_creds(self):
        client = hvac.Client(**self._get_vault_client_connection_options())
        creds_dict = client.read(
            join(self.settings_dict['VAULT']['MOUNT'], 'creds/%s' % self.settings_dict['VAULT']['ROLE'])
        )['data']
        client.close()
        return {
            'user': creds_dict['username'],
            'password': creds_dict['password']
        }

    def get_connection_params(self):
        settings_dict = self.settings_dict
        if not settings_dict.get('USER'):
            raise ImproperlyConfigured("DATABASE['USER'] is empty.!")

        if not settings_dict['NAME']:
            raise ImproperlyConfigured("DATABASE['NAME'] is empty. Nope!")
        if 'VAULT' not in settings_dict:
            raise ImproperlyConfigured("DATABASE['VAULT'] is empty. Nope!")

        _vault = settings_dict['VAULT']
        if not isinstance(_vault, dict):
            raise ImproperlyConfigured("DATABASE['VAULT'] is not a dict. Nope!")

        for k in REQUIRED_VAULT_OPTIONS:
            if not _vault.get(k, None):
                raise ImproperlyConfigured("DATABASE['VAULT'] has no required key: '%s'. Nope!" % k)

        conn_params = {'database': settings_dict['NAME']}
        conn_params.update(self._get_vault_creds())
        conn_params.update(settings_dict['OPTIONS'])
        conn_params.pop('isolation_level', None)
        if settings_dict['HOST']:
            conn_params['host'] = settings_dict['HOST']
        if settings_dict['PORT']:
            conn_params['port'] = settings_dict['PORT']
        return conn_params


@receiver(connection_created, sender=DatabaseWrapper, dispatch_uid='postgresql_connection_created')
def set_role(sender, connection, **kwargs):
    role = connection.settings_dict['USER']
    connection.cursor().execute('SET ROLE %s', (role,))
