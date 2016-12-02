/**
 *
 * 将下列内容添加到/var/www/initcloud_web/initcloud_web/render/static/management/app.js中
 */
            


          //snapshot
          .state("snapshot", {
                url: "/snapshot/",
                templateUrl: "/static/management/views/snapshot.html",
                data: {pageTitle: 'Snapshot'},
                controller: "SnapshotController",
                resolve: {
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/management/controllers/snapshot_ctrl.js'
                            ]
                        });
                    }]
                }
            })
