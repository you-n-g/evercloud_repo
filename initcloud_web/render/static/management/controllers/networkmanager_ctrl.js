/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('NetworkmanagerController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Networkmanager, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });

        $scope.networkmanagers = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.networkmanagers);

        $scope.networkmanager_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    Networkmanager.query(function(data){
                        $scope.networkmanagers = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.networkmanagers);
                    });
                }
            });



        var deleteNetworkmanagers = function(ids){

            $ngBootbox.confirm($i18next("networkmanager.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/networkmanager/batch-delete/", {ids: ids}).then(function(data){
                    if (data.OPERATION_STATUS == 1) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.networkmanager_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.modal_create_network = function () {
            $modal.open({
                templateUrl: '/static/management/views/network_create_wizard/network_wizard.html?t=' + Math.random(),
                controller: 'NetworkCreateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    networkmanager_table: function () {
                        return $scope.networkmanager_table;
                    },
                    quota: function (CommonHttpService) {
                        return CommonHttpService.get("/api/account/quota/");
                    },
                    tenants: function (CommonHttpService) {
                        return CommonHttpService.get("/api/tenants/");
                    },
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/assets/global/plugins/bootstrap-wizard/jquery.bootstrap.wizard.min.js',
                                '/static/management/scripts/create_network_wizard.js',
                            ]
                        });
                    }]
                }
            });
        };
        $scope.batchDelete = function(){

            deleteNetworkmanagers(function(){
                var ids = [];

                checkboxGroup.forEachChecked(function(Networkmanager){
                    if(networkmanager.checked){
                        ids.push(networkmanager.id);
                    }
                });

                return ids;
            });
        };

        $scope.delete = function(networkmanager){
            deleteNetworkmanagers([networkmanager.id]);
        };


        $scope.edit = function(networkmanager){

            $modal.open({
                templateUrl: 'update.html',
                controller: 'NetworkmanagerUpdateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    networkmanager_table: function () {
                        return $scope.networkmanager_table;
                    },
                    networkmanager: function(){return networkmanager}
                }
            });
        };

        $scope.openNewNetworkmanagerModal = function(){
            $modal.open({
                templateUrl: 'new-networkmanager.html',
                backdrop: "static",
                controller: 'NewNetworkmanagerController',
                size: 'lg',
                resolve: {
                    dataCenters: function(){
                        return DataCenter.query().$promise;
                    }
                }
            }).result.then(function(){
                $scope.networkmanager_table.reload();
            });
        };
    })


    .controller('NetworkCreateController',
        function($scope, $modalInstance, $i18next,
                 CommonHttpService, $modalInstance, networkmanager_table, ToastrService, NetworkmanagerForm, tenants){

        $scope.networkmanager_config = {
            "instance": 1,
            "pay_type": "hour",
            "pay_num": 1,
            "az":"",
            "aips": ""
        };


        $scope.month_options =  [];
        $scope.year_options =  [];

        for(var i=1; i<=10; i++){
            $scope.month_options.push({value: i, label: i + "月"});
        }

        for(var i=1; i<=5; i++){
            $scope.year_options.push({value: i, label: i + "年"});
        }

        $scope.tenants = tenants
        $scope.cancel = function () {
            $modalInstance.dismiss();
        };

        $scope.submit_click = function (networkmanager_config) {
            var post_data = {
                "network_name": networkmanager_config.network_name,
                "tenant": networkmanager_config.tenant,
                "physnet": networkmanager_config.physnet,
                "seg_id": networkmanager_config.seg_id,
                "status": networkmanager_config.status,
                "subnet_name": networkmanager_config.subnet_name,
                "cidr": networkmanager_config.cidr,
                "ip_version": networkmanager_config.ip_version,
                "gateway": networkmanager_config.gateway,
                "enable_gateway": networkmanager_config.enable_gateway,
                "enable_dhcp": networkmanager_config.enable_dhcp,
                "allocation_polls": networkmanager_config.allocation_polls,
                "dns_server": networkmanager_config.dns_server,
                "host_router": networkmanager_config.host_router,
            };
            CommonHttpService.post("/api/networkmanager/create/", post_data).then(function (data) {
                if (data.OPERATION_STATUS == 1) {
                    ToastrService.success(data.msg, $i18next("success"));
                    $modalInstance.dismiss();
                    network_table.reload();
                }
                else if (data.OPERATION_STATUS == 2) {
                    ToastrService.warning($i18next("op_forbid_msg"), $i18next("op_failed"));
                }
                else {
                    if (data.msg) {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                    else {
                        ToastrService.error($i18next("op_failed_msg"), $i18next("op_failed"));
                    }
                }
            });
        };

    }).factory('NetworkmanagerForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            networkmanagername: {
                                required: true,
                                remote: {
                                    url: "/api/networkmanager/is-name-unique/",
                                    data: {
                                        networkmanagername: $("#networkmanagername").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            networkmanagername: {
                                remote: $i18next('networkmanager.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#networkmanagerForm', config);
                }
            }
        }]).controller('NetworkmanagerUpdateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 networkmanager, networkmanager_table,
                 Networkmanager, UserDataCenter, networkmanagerForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.networkmanager = networkmanager = angular.copy(networkmanager);

            $modalInstance.rendered.then(networkmanagerForm.init);

            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            $modalInstance.rendered.then(function(){
                form = networkmanagerForm.init($scope.site_config.WORKFLOW_ENABLED);
            });
            $scope.submit = function(networkmanager){

                if(!$("#NetworkmanagerForm").validate().form()){
                    return;
                }

                networkmanager = ResourceTool.copy_only_data(networkmanager);


                CommonHttpService.post("/api/networkmanager/update/", networkmanager).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        networkmanager_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   ).factory('networkmanagerForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            networkmanagername: {
                                required: true,
                                remote: {
                                    url: "/api/networkmanager/is-name-unique/",
                                    data: {
                                        networkmanagername: $("#networkmanagername").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            networkmanagername: {
                                remote: $i18next('networkmanager.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#NetworkmanagerForm', config);
                }
            }
        }]);
