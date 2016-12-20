/**
 *
 * 将下列内容添加到/var/www/initcloud_web/initcloud_web/render/static/management/app.js中
 */
            


          //networkmanager
          .state("networkmanager", {
                url: "/networkmanager/",
                templateUrl: "/static/management/views/networkmanager.html",
                data: {pageTitle: 'Networkmanager'},
                controller: "NetworkmanagerController",
                resolve: {
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/management/controllers/networkmanager_ctrl.js'
                            ]
                        });
                    }]
                }
            })
