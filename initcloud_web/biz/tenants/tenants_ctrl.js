/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('TenantsController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Tenants, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });

        $scope.tenantss = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.tenantss);

        $scope.tenants_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    Tenants.query(function(data){
                        $scope.tenantss = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.tenantss);
                    });
                }
            });



        var deleteTenantss = function(ids){

            $ngBootbox.confirm($i18next("tenants.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/tenants/batch-delete/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.tenants_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.batchDelete = function(){

            deleteTenantss(function(){
                var ids = [];

                checkboxGroup.forEachChecked(function(Tenants){
                    if(tenants.checked){
                        ids.push(tenants.id);
                    }
                });

                return ids;
            });
        };

        $scope.delete = function(tenants){
            deleteTenantss([tenants.id]);
        };


        $scope.edit = function(tenants){

            $modal.open({
                templateUrl: 'update.html',
                controller: 'TenantsUpdateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    tenants_table: function () {
                        return $scope.tenants_table;
                    },
                    tenants: function(){return tenants}
                }
            });
        };

        $scope.openNewTenantsModal = function(){
            $modal.open({
                templateUrl: 'new-tenants.html',
                backdrop: "static",
                controller: 'NewTenantsController',
                size: 'lg',
                resolve: {
                    dataCenters: function(){
                        return DataCenter.query().$promise;
                    }
                }
            }).result.then(function(){
                $scope.tenants_table.reload();
            });
        };
    })


    .controller('NewTenantsController',
        function($scope, $modalInstance, $i18next,
                 CommonHttpService, ToastrService, TenantsForm, dataCenters){

            var form = null;
            $modalInstance.rendered.then(function(){
                form = TenantsForm.init($scope.site_config.WORKFLOW_ENABLED);
            });

            $scope.dataCenters = dataCenters;
            $scope.tenants = {is_resource_user: false, is_approver: false};
            $scope.is_submitting = false;
            $scope.cancel = $modalInstance.dismiss;
            $scope.create = function(){

                if(form.valid() == false){
                    return;
                }

                $scope.is_submitting = true;
                CommonHttpService.post('/api/tenants/create/', $scope.tenants).then(function(result){
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

   ).factory('TenantsForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            tenantsname: {
                                required: true,
                                remote: {
                                    url: "/api/tenants/is-name-unique/",
                                    data: {
                                        tenantsname: $("#tenantsname").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            tenantsname: {
                                remote: $i18next('tenants.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#tenantsForm', config);
                }
            }
        }]).controller('TenantsUpdateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 tenants, tenants_table,
                 Tenants, UserDataCenter, tenantsForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.tenants = tenants = angular.copy(tenants);

            $modalInstance.rendered.then(tenantsForm.init);

            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            $modalInstance.rendered.then(function(){
                form = tenantsForm.init($scope.site_config.WORKFLOW_ENABLED);
            });
            $scope.submit = function(tenants){

                if(!$("#TenantsForm").validate().form()){
                    return;
                }

                tenants = ResourceTool.copy_only_data(tenants);


                CommonHttpService.post("/api/tenants/update/", tenants).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        tenants_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   ).factory('tenantsForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            tenantsname: {
                                required: true,
                                remote: {
                                    url: "/api/tenants/is-name-unique/",
                                    data: {
                                        tenantsname: $("#tenantsname").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            tenantsname: {
                                remote: $i18next('tenants.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#TenantsForm', config);
                }
            }
        }]);
