/**
 *
 * 将下列内容添加到/var/www/initcloud_web/initcloud_web/render/static/management/app.js中
 */
            


          //ceilometer
          .state("ceilometer", {
                url: "/ceilometer/",
                templateUrl: "/static/management/views/ceilometer.html",
                data: {pageTitle: 'Ceilometer'},
                controller: "CeilometerController",
                resolve: {
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/management/controllers/ceilometer_ctrl.js'
                            ]
                        });
                    }]
                }
            })
