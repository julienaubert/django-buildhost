import StringIO
from fabric.api import *
from fabric.colors import green, red
from fabric.contrib.files import upload_template, exists, sed
from bh.utils import as_bool
from bh.user import setup_env_for_user

@task
def python():
    """ compile and install python
    """
    setup_env_for_user(env.user)
    version = env.PYTHON.replace('Python-', '')
    run('mkdir -p %(admin_home_dir)s/~build' % env)
    with cd(env.build):
        if not exists('%(packages_cache)s/%(PYTHON)s.tgz' % env):
            with cd(env.packages_cache):
                run('wget http://www.python.org/ftp/python/%(PYTHON)s/Python-%(PYTHON)s.tgz' % env)
        run('tar -xzf %(packages_cache)s/Python-%(PYTHON)s.tgz' % env)
        with cd('Python-%(PYTHON)s' % env):
            run('./configure --prefix=%(base)s --enable-shared --with-threads' % env)
            run('make clean')
            run('make')
            run('make install')

    # check local install
    out = run('python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"')
    assert out.startswith("%(base)s/" % env), 'Error: `%s` ' % out

    # checl ssl support
    out = run('python -c "import socket;print socket.ssl"')
    assert out.startswith("<function ssl at "), out

    run('wget http://python-distribute.org/distribute_setup.py')
    run('python distribute_setup.py')
    run('easy_install -U pip')
    run('pip install ipython')

def bin_installed(what):
    with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
        out = run('which {}'.format(what))
        return out.startswith('{base}/bin/{what}'.format(base=env.base, what=what))

def gem_installed(what):
    with settings(hide('warnings', 'running', 'stdout', 'stderr'), warn_only=True):
        out = run('gem list {} -i'.format(what))
        return out == 'true'

@task
def cmake():
    setup_env_for_user(env.user)
    if bin_installed('cmake'):
        print "cmake already installed"
        return
    run('mkdir -p {admin_home_dir}/~build'.format(**env))
    env.CMAKE = 'cmake-2.8.11.2'
    with cd(env.build):
        if not exists('{packages_cache}/{CMAKE}.tar.gz'.format(**env)):
            run('wget http://www.cmake.org/files/v2.8/{CMAKE}.tar.gz -P {packages_cache}/'.format(**env))
        run('tar -xzf {packages_cache}/{CMAKE}.tar.gz'.format(**env))
        with cd(env.CMAKE):
            run('./bootstrap '
                ' --prefix={base}'
                ' --datadir={base}/share/CMake'
                ' --docdir={base}/doc/CMake'
                ' --mandir={base}/man'
                ''.format(**env))
            run('make clean')
            run('make')
            run('make install')
        run('rm -fr {CMAKE}'.format(**env))

@task
def mysql():
    """
    compile and install mysql
    """
    setup_env_for_user(env.user)
    if bin_installed('mysql'):
        print "mysql already installed"
        return
    if not bin_installed('cmake'):
        execute(cmake)
    run('mkdir -p {admin_home_dir}/~build'.format(**env))
    env.MYSQL = 'mysql-5.7.2-m12'
    with cd(env.build):
        if not exists('{packages_cache}/{MYSQL}.tar.gz'.format(**env)):
            run('wget http://mysql.mirror.facebook.net/MySQL-5.7/{MYSQL}.tar.gz -P {packages_cache}'.format(**env))
        run('tar -xzf {packages_cache}/{MYSQL}.tar.gz'.format(**env))
        with cd(env.MYSQL):
            run('mkdir -p {base}/var/lib')
            run('cmake '
                ' -DCMAKE_INSTALL_PREFIX={base}'
                ' -DMYSQL_UNIX_ADDR={base}/tmp/mysql.sock'
                ' -DMYSQL_DATADIR={base}/var/lib/mysql'
                ' .'
                ''.format(**env))
            run('make clean')
            run('make')
            run('make install')
        run('rm -fr {MYSQL}'.format(**env))
    if bin_installed('ruby'):
        run('gem install mysql2')
    run('{base}/scripts/mysql_install_db '
        ' --user={user} '
        ' --random-passwords'
        ' --force'
        ' --basedir={base}'
        ' --skip-name-resolve'
        ''.format(**env))
    run('echo \'basedir={base}\' >> {base}/my.cnf'.format(**env))
    run('echo \'datadir={base}/var/lib/mysql\' >> {base}/my.cnf'.format(**env))
    run('echo \'port={env.MYSQL_PORT}\' >> {base}/my.cnf'.format(**env))
    run('cd {base}/mysql-test ; perl mysql-test-run.pl'.format(**env))


@task
def ruby():
    """
    compile and install ruby
    """
    setup_env_for_user(env.user)
    if bin_installed('ruby'):
        print "ruby already installed"
        return
    run('mkdir -p {admin_home_dir}/~build'.format(**env))
    env.RUBY = 'ruby-2.0.0-p247'
    with cd(env.build):
        if not exists('{packages_cache}/{RUBY}.tar.gz'.format(**env)):
            run('wget http://cache.ruby-lang.org/pub/ruby/2.0/{RUBY}.tar.gz -P {packages_cache}'.format(**env))
        run('tar -xzf {packages_cache}/{RUBY}.tar.gz'.format(**env))
        with cd(env.RUBY):
            run('./configure '
                ' --prefix={base}'
                ' --exec_prefix={base}'
                ' --bindir={base}/bin'
                ' --sbindir={base}/bin'
                ' --libexecdir={base}/lib/ruby'
                ' --mandir={base}/man'
                ' --sysconfdir={base}/etc/httpd/conf'
                ' --datadir={base}/var/www'
                ' --includedir={base}/lib/include/ruby'
                ' --localstatedir={base}/var/run'
                ''.format(**env))
            run('make clean')
            run('make')
            run('make install')
        run('rm -fr {RUBY}'.format(**env))
    if bin_installed('mysql'):
        run('gem install mysql2')


@task
def imagemagick():
    """
    compile and install imagemagick
    """
    setup_env_for_user(env.user)
    if bin_installed('animate'):
        print "imagemagick already installed"
        return
    run('mkdir -p {admin_home_dir}/~build'.format(**env))
    env.IMAGEMAGICK = 'ImageMagick-6.8.7-0'
    with cd(env.build):
        if not exists('{packages_cache}/{IMAGEMAGICK}.tar.gz'.format(**env)):
            run('wget http://www.imagemagick.org/download/{IMAGEMAGICK}.tar.gz -P {packages_cache}'.format(**env))
        run('tar -xzf {packages_cache}/{IMAGEMAGICK}.tar.gz'.format(**env))
        with cd(env.IMAGEMAGICK):
            run('./configure '
                ' --prefix={base}'
                ' --exec_prefix={base}'
                ''.format(**env))
            run('make clean')
            run('make')
            run('make install')
        run('rm -fr {IMAGEMAGICK}'.format(**env))

@task
def curl():
    setup_env_for_user(env.user)
    if bin_installed('curl'):
        print "curl already installed"
        return
    run('mkdir -p {admin_home_dir}/~build'.format(**env))
    env.CURL = 'curl-7.32.0'
    with cd(env.build):
        if not exists('{packages_cache}/{CURL}.tar.gz'.format(**env)):
            run('wget http://curl.haxx.se/download/{CURL}.tar.gz -P {packages_cache}'.format(**env))
        run('tar -xzf {packages_cache}/{CURL}.tar.gz'.format(**env))
        with cd(env.CURL):
            run('./configure '
                ' --prefix={base}'
                ' --exec_prefix={base}'
                ''.format(**env))
            run('make clean')
            run('make')
            run('make install')
        run('rm -fr {CURL}'.format(**env))

@task
def redmine(mysql_port, http_port):
    setup_env_for_user(env.user)
    if not bin_installed('apachectl'):
        execute(apache)
    if not bin_installed('animate'):
        execute(imagemagick)
    if not bin_installed('ruby'):
        execute(ruby)
    if not gem_installed('rails'):
        run('gem install rails')
    if not gem_installed('bundler'):
        run('gem install bundler')
    if not bin_installed('mysql'):
        execute(mysql)
    with settings(warn_only=True):
        run('mysqld_safe &')
    run('mysql -u root -e "CREATE DATABASE redmine CHARACTER SET utf8;"')
    run('mysql -u root -e "CREATE USER \'redmine\'@\'localhost\' IDENTIFIED BY \'password_123\';"')
    run('mysql -u root -e "GRANT ALL PRIVILEGES ON redmine.* TO \'redmine\'@\'localhost\';"')
    env.REDMINE = 'redmine-2.3.3'
    if not exists('{packages_cache}/{REDMINE}.tar.gz'.format(**env)):
        run('wget http://rubyforge.org/frs/download.php/77138/{REDMINE}.tar.gz -P {packages_cache}'.format(**env))
    with cd('{base}/var/www/'.format(**env)):
        run('tar -xzf {packages_cache}/{REDMINE}.tar.gz'.format(**env))
        with cd(env.REDMINE):
            run('cp config/database.yml.example config/database.yml')
            run('echo \'production:\' >> config/database.yml')
            run('echo \'  adapter: mysql2\' >> config/database.yml')
            run('echo \'  database: redmine\' >> config/database.yml')
            run('echo \'  host: localhost\' >> config/database.yml')
            run('echo \'  port: {MYSQL_PORT}\' >> config/database.yml'.format(**env))
            run('echo \'  username: redmine\' >> config/database.yml')
            run('echo \'  password: password_123\' >> config/database.yml')
            run('PKG_CONFIG_PATH={base}/lib/pkgconfig/:$PKG_CONFIG_PATH '
                'bundle install --without development test'
                ''.format(**env))
            run('rake generate_secret_token')
            run('RAILS_ENV=production rake db:migrate')
            run('RAILS_ENV=production REDMINE_LANG=en rake redmine:load_default_data')
    if not gem_installed('passenger'):
        run('gem install passenger')
    execute(curl)
    run('passenger-install-apache2-module')
    httpd_conf = ("""
                    ServerRoot "/opt/cv_instances/cv6"
                    Listen {http_port}

                    ServerAdmin you@example.com
                    ServerName 10.11.40.173:{http_port}

                    DocumentRoot "{base}/var/www/{REDMINE}/public"
                    <Directory />
                        Options FollowSymLinks
                        AllowOverride None
                        Order deny,allow
                        Deny from all
                    </Directory>
                    <Directory "{base}/var/www/{REDMINE}/public">
                        Options Indexes FollowSymLinks
                        AllowOverride None
                        Order allow,deny
                        Allow from all
                    </Directory>

                    <IfModule dir_module>
                        DirectoryIndex index.html
                    </IfModule>

                    <FilesMatch "^\.ht">
                        Order allow,deny
                        Deny from all
                        Satisfy All
                    </FilesMatch>

                    ErrorLog "var/run/logs/error_log"
                    LogLevel warn

                    <IfModule log_config_module>
                        LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
                        LogFormat "%h %l %u %t \"%r\" %>s %b" common

                        <IfModule logio_module>
                          LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %I %O" combinedio
                        </IfModule>

                        CustomLog "var/run/logs/access_log" common
                        #CustomLog "var/run/logs/access_log" combined
                    </IfModule>

                    <IfModule alias_module>
                        ScriptAlias /cgi-bin/ "{base}/var/www/cgi-bin/"
                    </IfModule>

                    <Directory "{base}/var/www/cgi-bin">
                        AllowOverride None
                        Options None
                        Order allow,deny
                        Allow from all
                    </Directory>

                    DefaultType text/plain

                    <IfModule mime_module>
                        TypesConfig etc/httpd/conf/mime.types
                    </IfModule>


                    # Secure (SSL/TLS) connections
                    #Include etc/httpd/conf/extra/httpd-ssl.conf
                    #
                    # Note: The following must must be present to support
                    #       starting without SSL on platforms with no /dev/random equivalent
                    #       but a statically compiled-in mod_ssl.
                    #
                    <IfModule ssl_module>
                    SSLRandomSeed startup builtin
                    SSLRandomSeed connect builtin
                    </IfModule>

                    LoadModule passenger_module {base}/lib/ruby/gems/2.0.0/gems/passenger-4.0.19/buildout/apache2/mod_passenger.so
                    PassengerRoot {base}/lib/ruby/gems/2.0.0/gems/passenger-4.0.19
                    PassengerDefaultRuby {base}/bin/ruby
                  """).format(**env)
    with cd('{base}/etc/httpd/conf/'.format(base=env.base, http_port=http_port)):
        run('rm httpd.conf')
        run('echo \'{}\' > httpd.conf'.format(httpd_conf))
    run('apachectl restart')


@task
def apache():
    """ compile and install apache
    """
    setup_env_for_user(env.user)

    run('mkdir -p %(admin_home_dir)s/~build' % env)
    run('mkdir -p %(admin_home_dir)s/etc/httpd/conf.d' % env)
    with cd(env.build):
        run('tar -xzf %(packages_cache)s/%(APACHE)s.tar.gz' % env)
        with cd(env.APACHE):
            run('./configure '\
                ' --prefix=%(base)s'\
                ' --exec_prefix=%(base)s'\
                ' --bindir=%(base)s/bin'\
                ' --sbindir=%(base)s/bin'\
                ' --libexecdir=%(base)s/lib/apache'\
                ' --mandir=%(base)s/man'\
                ' --sysconfdir=%(base)s/etc/httpd/conf'\
                ' --datadir=%(base)s/var/www'\
                ' --includedir=%(base)s/lib/include/apache'\
                ' --localstatedir=%(base)s/var/run'\
                ' --enable-rewrite'\
                #                ' --enable-rewrite=shared'\
                #                ' --enable-mods-shared=most'\
                ' --with-included-apr'\
                ' --enable-ssl'
            % env)
            run('make clean')
            run('make')
            run('make install')


@task
def sqlite():
    setup_env_for_user(env.user)
    run('mkdir -p %(admin_home_dir)s/~build' % env)
    with cd(env.build):
        run('tar -xzf %(packages_cache)s/%(SQLITE)s.tar.gz' % env)
        with cd(env.SQLITE):
            run('./configure '\
                ' --prefix=%(base)s'\
                ' --exec_prefix=%(base)s'\
                ' --bindir=%(base)s/bin'\
                ' --sbindir=%(base)s/bin' % env )
            run('make')
            run('make install')
            run('sqlite3 -version')

#            run("cp uwsgi %(base)s/bin/uwsgi" % env)

@task
def uwsgi():
    """ compile and install uwsgi
    """
    setup_env_for_user(env.user)
    if not exists('%(packages_cache)s/uwsgi-%(UWSGI)s.tar.gz' % env):
        with cd(env.packages_cache):
            run('wget http://projects.unbit.it/downloads/uwsgi-%(UWSGI)s.tar.gz' % env)

    run('mkdir -p %(admin_home_dir)s/~build' % env)
    with cd(env.build):
        run('tar -xzf %(packages_cache)s/uwsgi-%(UWSGI)s.tar.gz' % env)
        with cd('uwsgi-%(UWSGI)s' % env):
            run('python uwsgiconfig.py --build' % env)
            run("cp uwsgi %(base)s/bin/uwsgi" % env)


@task
def modwsgi():
    """ compile and install modwsgi
    """
    setup_env_for_user(env.user)
    run('mkdir -p %(admin_home_dir)s/~build' % env)
    with cd(env.build):
        run('tar xvfz %(packages_cache)s/%(MOD_WSGI)s.tar.gz' % env)
        with cd(env.MOD_WSGI):
            run('./configure --with-apxs=%(base)s/bin/apxs --with-python=%(base)s/bin/python' % env)
            run('make clean')
            run('make')
            run('make install')


@task
def sqlplus():
    setup_env_for_user(env.user)
    tar = env.deps['sqlplus']
    run('rm -fr ~/~build/sqlplus')
    run('mkdir -p ~/~build/sqlplus')
    with settings(tar=tar):
        put('%(tarballs)s/%(tar)s' % env, '~/~build/sqlplus/')
    with cd('~/~build/sqlplus'):
        run('ls')
        run('unzip %s' % tar)
        run('cp instantclient_11_2/* ~/oracle/instantclient_11_2/')
        run('mv ~/oracle/instantclient_11_2/sqlplus ~/bin/sqlplus')
    run('sqlplus  -V') # simple check


#@task
#def oracle():
#    """ compile and install oracle drivers
#    """
#    setup_env_for_user(env.user)
#    run('mkdir -p %(admin_home_dir)s/~build' % env)
#    #put('%(tarball_dir)s/instantclient-*' % env, env.packages_cache)
#    with cd(env.base):
#        run('rm -fr oracle*')
#        run('mkdir -p oracle')
#        with settings(finder="find %(packages_cache)s -regextype posix-extended -type f -regex '%(packages_cache)s/instantclient-(sdk|basic-linux|sqlplus).*%(ORACLE)s.*'" % env):
#            with cd('oracle'):
#                arch = run('uname -i')
#                if arch == 'x86_64':
#                    run('%(finder)s -exec unzip "{}" \;' % env)
#                elif arch == 'i386':
#                    raise Exception('Not supported')
#
#                env.oracle_home = run('find $PWD -type d -iname "instant*"' % env)
#
#    sed("~/.bash_profile", "export LD_LIBRARY_PATH=.*", "export LD_LIBRARY_PATH=$SITE_ENV/lib:%(oracle_home)s:" % env)
#    sed("~/bin/activate", "export ORACLE_HOME=.*", "export ORACLE_HOME=%(oracle_home)s:" % env)
#
#    run('pip install -I cx_Oracle')
#    run('mkdir -p ~/logs/oracle')
#    run('ln -s ~/logs/oracle %(oracle_home)s/log' % env)
#    # test
#    out = run('python -c "import cx_Oracle;print(222)"')
#    assert out.startswith("222")

@task
def oracle():
    """ compile and install oracle drivers
    """
    setup_env_for_user(env.user)
    run('mkdir -p %(admin_home_dir)s/~build' % env)
    with cd(env.base):
        run('rm -fr oracle*')
        run('mkdir -p oracle')
        with cd('oracle'):
            arch = run('uname -i')
            if arch == 'x86_64':
                run('find %(packages_cache)s -name "instantclient*86-64*" -exec unzip "{}" \;' % env)
            elif arch == 'i386':
                run('find %(packages_cache)s -name "instantclient*" -name "*86-64*" -exec unzip "{}" \;' % env)
            with cd('instantclient_*'):
                run('ln -sf libclntsh.so.11.1 libclntsh.so')

    env.oracle_home = run('find $PWD -type d -iname "instant*"' % env)
    sed("~/.bash_profile", "export LD_LIBRARY_PATH=.*", "export LD_LIBRARY_PATH=$SITE_ENV/lib:%(oracle_home)s:" % env)
    sed("~/bin/activate", "export ORACLE_HOME=.*", "export ORACLE_HOME=%(oracle_home)s:" % env)


    assert exists('%(oracle_home)s/libclntsh.so' % env)
    run('pip install cx_Oracle')
    run('mkdir -p ~/logs/oracle')
    run('ln -s ~/logs/oracle %(base)s/oracle/instantclient_11_2/log' % env)
    # test
    out = run('python -c "import cx_Oracle;print(222)"')
    assert out.startswith("222")


@task
def nginx(version=None):
    """ compile and install nginx
    """
    if version:
        env.NGINX = version
    setup_env_for_user()
    with cd(env.build):
        with cd(env.packages_cache):
            if not exists('%(packages_cache)s/nginx-%(NGINX)s.tar.gz' % env):
                run('wget http://nginx.org/download/nginx-%(NGINX)s.tar.gz' % env)

            if not exists('%(packages_cache)s/pcre-%(PCRE)s.tar.gz' % env):
                run('wget ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-%(PCRE)s.tar.gz' % env)

            if not exists('%(packages_cache)s/uwsgi-%(UWSGI)s.tar.gz' % env):
                run('wget http://projects.unbit.it/downloads/uwsgi-%(UWSGI)s.tar.gz' % env)

        run("tar -xzf %(packages_cache)s/nginx-%(NGINX)s.tar.gz" % env)
        run("tar -xzf %(packages_cache)s/pcre-%(PCRE)s.tar.gz" % env)
        run("tar -xzf %(packages_cache)s/uwsgi-%(UWSGI)s.tar.gz" % env)

        with cd('nginx-%(NGINX)s' % env):
            run("./configure --prefix=%(base)s" \
                " --sbin-path=%(base)s/bin" \
                " --pid-path=%(base)s/run/nginx.pid" \
                " --lock-path=%(base)s/run/nginx.lck" \
                " --user=nginx" \
                " --group=%(group)s" \
                " --with-debug " \
                    #                " --with-google_perftools_module"\
                " --with-select_module" \
                " --with-http_ssl_module" \
                " --with-http_gzip_static_module" \
                " --with-http_stub_status_module" \
                " --with-http_realip_module" \
                " --with-http_ssl_module" \
                " --with-http_sub_module" \
                " --with-http_addition_module" \
                " --with-http_flv_module" \
                " --with-http_addition_module" \
                " --with-file-aio" \
                " --with-sha1-asm" \
                " --http-proxy-temp-path=%(base)s/tmp/proxy/" \
                " --http-client-body-temp-path=%(base)s/tmp/client/" \
                " --http-fastcgi-temp-path=%(base)s/tmp/fcgi/" \
                " --http-uwsgi-temp-path=%(base)s/tmp/uwsgi/" \
                " --http-scgi-temp-path=%(base)s/tmp/scgi/" \
                " --http-log-path=%(base)s/logs/nginx/access.log" \
                " --error-log-path=%(base)s/logs/nginx/error.log" \
                " --with-pcre=../pcre-%(PCRE)s" % env
            )
            run("make")
            run("make install")


@task
def check():
    """ check installation of the servers/appliance
    """
    setup_env_for_user()

    def _test(cmd, where):
        print 'Checking `%s`..' % cmd,
        with settings(warn_only=True):
            out = run(cmd)
            if out.startswith(where):
                print green('Ok')
            else:
                print red("FAIL!!"), out

    puts('Checking installation...')

    with hide('everything'):
        _test('which httpd', '%(base)s/bin/httpd' % env)
        _test('which nginx', '%(base)s/bin/nginx' % env)
        _test('which uwsgi', '%(base)s/bin/uwsgi' % env)
        _test('which python', '%(base)s/bin/python' % env)
        _test('which pip', '%(base)s/bin/pip' % env)

        _test('python -V', 'Python 2.7.2')
        _test('python -c "import cx_Oracle;print(\'cx_Oracle imported\')"', 'cx_Oracle imported')
        _test('python -c "import socket;print socket.ssl"', '<function ssl at')

        print 'Checking $PATH..',
        out = run('echo $PATH')
        assert out.startswith("%(base)s/bin:%(base)s/apache/bin" % env), out
        print green('Ok (%s)' % out)


@task
def copy_cmds():
    """ initalize remote admin home directory
    """
    upload_template("tpls/sbin/all_env_command.sh", "%(PREFIX)s/sbin" % env, env, use_jinja=True)
    run('chmod +x %(PREFIX)s/sbin/*.sh' % env)

@task
def postgresql():
    setup_env_for_user(env.user)
    with cd(env.build):
        run('wget http://ftp.postgresql.org/pub/source/v%(POSTGRES)s/postgresql-%(POSTGRES)s.tar.bz2' % env)
        run('tar -xf postgresql-%(POSTGRES)s.tar.bz2' % env)

        with cd('postgresql-%(POSTGRES)s' % env):
            run('./configure --prefix=%(base)s' % env)
            run('make')
            run('make install')
        run('rm -fr postgresql-%(POSTGRES)s' % env)



def mysql():
    with cd(env.packages_cache):
        if not exists('%(packages_cache)s/mysql-%(MYSQL)s.tar.gz' % env):
                run('wget http://nginx.org/download/mysql-%(MYSQL)s.tar.gz' % env)

    with cd('~/mysql-%(MYSQL)s' % env):
        opts = " ".join([" -DWITH_ARCHIVE_STORAGE_ENGINE=1",
                         " -DWITH_FEDERATED_STORAGE_ENGINE=1",
                         " -DWITH_BLACKHOLE_STORAGE_ENGINE=1",
                         " -DMYSQL_DATADIR={0}/data/",
                         " -DCMAKE_INSTALL_PREFIX={0}/server",
                         #" -DCURSES_LIBRARY=/opt/ncurses/lib/libncurses.a ",
                         #" -DCURSES_INCLUDE_PATH=/opt/ncurses/include/",
                         #" -DHAVE_LIBAIO_H=/opt/libaio/include/ ",
                         " -DINSTALL_LAYOUT=STANDALONE ",
                         " -DENABLED_PROFILING=ON ",
                         " -DMYSQL_MAINTAINER_MODE=OFF",
                         " -DWITH_DEBUG=OFF ",
                         " -DDEFAULT_CHARSET=utf8",
                         " -DENABLED_LOCAL_INFILE=TRUE",
                         " -DWITH_ZLIB=bundled"]).format('~')

        run('cmake %s' % opts)
        run('./configure --with-charset=utf8 --with-collation=utf8_unicode_ci ')
        run('make ')
        run('make mysqlclient libmysql')
        run('make install')
        run('mkdir -p ~/log')
        put(StringIO.StringIO(MYSQL_CONFIG), "~/server/my.cnf")
        run('scripts/mysql_install_db --user=mysql --explicit_defaults_for_timestamp')
        run('./server/bin/mysql  -e "GRANT ALL PRIVILEGES ON *.* TO \'root\'@\'%\' IDENTIFIED BY \'123\' WITH GRANT OPTION;"')
        run('./server/bin/mysql  -e "GRANT ALL PRIVILEGES ON *.* TO \'root\'@\'localhost\' WITH GRANT OPTION;"')

MYSQL_CONFIG = r"""
[mysqld]
datadir={home}/server/data
port=3306
log-error = {home}/log/mysqld.error.log
#character-set-server=utf8
#collation-server=utf8_unicode_ci
#server-id=1382004430

[mysql.server]
user=mysql
basedir={home}/server

""".format(home='/opt/host_services/mysql', host='*', )

MYSQL_START="~/server/bin/mysqld_safe --defaults-file=~/server/my.cnf &"
MYSQL_STOP="~/server/bin/mysqladmin -u root -p shutdown"

@task
@hosts('mysql@pydev.wfp.org')
def config_mysql():
    run('mkdir -p ~/log')

    put(StringIO.StringIO(MYSQL_CONFIG), "~/server/my.cnf")
    put(StringIO.StringIO(MYSQL_START), "~/start.sh")
    put(StringIO.StringIO(MYSQL_STOP), "~/stop.sh")

    run("chmod +x ~/start.sh ~/stop.sh")

@task
def install():
    """ install all required servers/appliance

    this command
    """
    setup_env_for_user(env.user)
    execute(python)
#    execute(apache)
#    execute(modwsgi)

#    execute(oracle)
#    execute(uwsgi)
#    execute(ngnix)
