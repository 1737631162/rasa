#!/bin/sh
hook_url=${HOOK_URL:-"http://10.64.21.47:8888/hook/hook.sh"}
enable_config_center=${ENABLE_CONFIG_CENTER:-"false"}
get_app_config()
{
        base_config_svn_url=${BASE_CONFIG_SVN_URL:-"http://10.64.21.74:8888/svn/config-center/trunk"}
        svn_username=${SVN_USERNAME:-"guest"}
        svn_password=${SVN_PASSWORD:-"guest"}
        if [ 'x'$APP_NAME = 'x' ]; then
           echo '*******************请设置APP_NAME环境变量*******************'
           exit 1
        fi
        if [ 'x'$PRO_ENV = 'x' ]; then
           echo '*******************请设置PRO_ENV环境变量*******************'
           exit 1
        fi

        if [ 'x'$CONFIG_SVN_URL = 'x' ]; then
           CONFIG_SVN_URL="$base_config_svn_url/$PRO_ENV/$APP_NAME"
        fi
        echo yes | svn checkout --username $svn_username --password $svn_password $CONFIG_SVN_URL  /home
        if [ $? -ne 0 ]; then
          echo '*******************配置文件下载失败*******************'
          exit 2
        fi
        /bin/cp -rf /home/* /opt/vbot-intent-task-di/rasa
}
if [ 'x'$enable_config_center = 'xtrue' ]; then
   get_app_config
fi
