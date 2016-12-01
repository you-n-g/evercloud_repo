/**
 *
 * 将下列内容添加到/var/www/initcloud_web/initcloud_web/render/static/management/app.js中
 */
            


          //templatemanager
          .state("templatemanager", {
                url: "/templatemanager/",
                templateUrl: "/static/management/views/templatemanager.html",
                data: {pageTitle: 'Templatemanager'},
                controller: "TemplatemanagerController",
                resolve: {
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/management/controllers/templatemanager_ctrl.js'
                            ]
                        });
                    }]
                }
            })
