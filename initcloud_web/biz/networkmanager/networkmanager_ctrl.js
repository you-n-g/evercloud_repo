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
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.networkmanager_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
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


    .controller('NewNetworkmanagerController',
        function($scope, $modalInstance, $i18next,
                 CommonHttpService, ToastrService, NetworkmanagerForm, dataCenters){

            var form = null;
            $modalInstance.rendered.then(function(){
                form = NetworkmanagerForm.init($scope.site_config.WORKFLOW_ENABLED);
            });

            $scope.dataCenters = dataCenters;
            $scope.networkmanager = {is_resource_user: false, is_approver: false};
            $scope.is_submitting = false;
            $scope.cancel = $modalInstance.dismiss;
            $scope.create = function(){

                if(form.valid() == false){
                    return;
                }

                $scope.is_submitting = true;
                CommonHttpService.post('/api/networkmanager/create/', $scope.networkmanager).then(function(result){
                    if(result.success){
                        ToastrService.success(result.msg, $i18next("success"));
                        $modalInstance.close();
                    } else {
                        ToastrService.error(result.msg, $i18next("op_failed"));
                    }
                    $scope.is_submitting = true;
                }).finally(function(){
                    $scope.is_submitting = false;
                });
            };
        }

   ).factory('NetworkmanagerForm', ['ValidationTool', '$i18next',
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
