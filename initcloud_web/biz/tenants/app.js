/**
 *
 * 将下列内容添加到/var/www/initcloud_web/initcloud_web/render/static/management/app.js中
 */
            


          //tenants
          .state("tenants", {
                url: "/tenants/",
                templateUrl: "/static/management/views/tenants.html",
                data: {pageTitle: 'Tenants'},
                controller: "TenantsController",
                resolve: {
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/management/controllers/tenants_ctrl.js'
                            ]
                        });
                    }]
                }
            })
