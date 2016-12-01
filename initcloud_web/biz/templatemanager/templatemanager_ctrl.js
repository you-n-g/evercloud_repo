/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('TemplatemanagerController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Templatemanager, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });

        $scope.templatemanagers = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.templatemanagers);

        $scope.templatemanager_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    Templatemanager.query(function(data){
                        $scope.templatemanagers = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.templatemanagers);
                    });
                }
            });



        var deleteTemplatemanagers = function(ids){

            $ngBootbox.confirm($i18next("templatemanager.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/templatemanager/batch-delete/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.templatemanager_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.batchDelete = function(){

            deleteTemplatemanagers(function(){
                var ids = [];

                checkboxGroup.forEachChecked(function(Templatemanager){
                    if(templatemanager.checked){
                        ids.push(templatemanager.id);
                    }
                });

                return ids;
            });
        };

        $scope.delete = function(templatemanager){
            deleteTemplatemanagers([templatemanager.id]);
        };


        $scope.edit = function(templatemanager){

            $modal.open({
                templateUrl: 'update.html',
                controller: 'TemplatemanagerUpdateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    templatemanager_table: function () {
                        return $scope.templatemanager_table;
                    },
                    templatemanager: function(){return templatemanager}
                }
            });
        };

        $scope.openNewTemplatemanagerModal = function(){
            $modal.open({
                templateUrl: 'new-templatemanager.html',
                backdrop: "static",
                controller: 'NewTemplatemanagerController',
                size: 'lg',
                resolve: {
                    dataCenters: function(){
                        return DataCenter.query().$promise;
                    }
                }
            }).result.then(function(){
                $scope.templatemanager_table.reload();
            });
        };
    })


    .controller('NewTemplatemanagerController',
        function($scope, $modalInstance, $i18next,
                 CommonHttpService, ToastrService, TemplatemanagerForm, dataCenters){

            var form = null;
            $modalInstance.rendered.then(function(){
                form = TemplatemanagerForm.init($scope.site_config.WORKFLOW_ENABLED);
            });

            $scope.dataCenters = dataCenters;
            $scope.templatemanager = {is_resource_user: false, is_approver: false};
            $scope.is_submitting = false;
            $scope.cancel = $modalInstance.dismiss;
            $scope.create = function(){

                if(form.valid() == false){
                    return;
                }

                $scope.is_submitting = true;
                CommonHttpService.post('/api/templatemanager/create/', $scope.templatemanager).then(function(result){
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

   ).factory('TemplatemanagerForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            templatemanagername: {
                                required: true,
                                remote: {
                                    url: "/api/templatemanager/is-name-unique/",
                                    data: {
                                        templatemanagername: $("#templatemanagername").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            templatemanagername: {
                                remote: $i18next('templatemanager.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#templatemanagerForm', config);
                }
            }
        }]).controller('TemplatemanagerUpdateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 templatemanager, templatemanager_table,
                 Templatemanager, UserDataCenter, templatemanagerForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.templatemanager = templatemanager = angular.copy(templatemanager);

            $modalInstance.rendered.then(templatemanagerForm.init);

            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            $modalInstance.rendered.then(function(){
                form = templatemanagerForm.init($scope.site_config.WORKFLOW_ENABLED);
            });
            $scope.submit = function(templatemanager){

                if(!$("#TemplatemanagerForm").validate().form()){
                    return;
                }

                templatemanager = ResourceTool.copy_only_data(templatemanager);


                CommonHttpService.post("/api/templatemanager/update/", templatemanager).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        templatemanager_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   ).factory('templatemanagerForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            templatemanagername: {
                                required: true,
                                remote: {
                                    url: "/api/templatemanager/is-name-unique/",
                                    data: {
                                        templatemanagername: $("#templatemanagername").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            templatemanagername: {
                                remote: $i18next('templatemanager.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#TemplatemanagerForm', config);
                }
            }
        }]);
