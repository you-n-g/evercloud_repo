/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('InstancemanageController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Instancemanage, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });

        var need_confirm = true;
        var no_confirm = false;

        var post_action = function (ins, action) {
            var post_data = {
                "action": action,
                "instance": ins.id
            };

            CommonHttpService.post("/api/instances/" + ins.id + "/action/", post_data).then(function (data) {
                if (data.OPERATION_STATUS == 1) {
                    $scope.instance_table.reload();
                } else if (data.OPERATION_STATUS == 2) {
                    var msg = data.MSG || $i18next("op_forbid_msg");
                    ToastrService.warning(msg, $i18next("op_failed"));
                } else {
                    var msg = data.MSG || $i18next("op_failed_msg");
                    ToastrService.error(msg, $i18next("op_failed"));
                }
            });
        };
        var do_instance_action = function (ins, action, need_confirm) {
            if (need_confirm) {
                bootbox.confirm($i18next("instance.confirm_" + action) + "[" + ins.name + "]", function (confirm) {
                    if (confirm) {
                        post_action(ins, action);
                    }
                });
            }
            else {
                post_action(ins, action);
            }
        };

        var instance_novnc_console = function (ins) {
            var post_data = {
                "action": "novnc_console",
                "instance": ins.id
            };
            $modal.open({
                templateUrl: 'novnc_console.html',
                controller: 'InstanceNOVNCController',
                backdrop: "static",
                size: 'lg',
                scope: $scope,
                resolve: {
                    'novnc_console': function (CommonHttpService) {
                        return CommonHttpService.post("/api/instances/" + ins.id + "/action/", post_data);
                    }
                }
            });
        };


        var instance_vnc_console = function (ins) {
            var post_data = {
                "action": "vnc_console",
                "instance": ins.id
            };
            $modal.open({
                templateUrl: 'vnc_console.html',
                controller: 'InstanceVNCController',
                backdrop: "static",
                size: 'lg',
                scope: $scope,
                resolve: {
                    'vnc_console': function (CommonHttpService) {
                        return CommonHttpService.post("/api/instances/" + ins.id + "/action/", post_data);
                    }
                }
            });
        };
        var instance_spice_console = function (ins) {
            var post_data = {
                "action": "spice_console",
                "instance": ins.id
            };
            $scope.test = "test"
            $modal.open({
                templateUrl: 'spice_console.html',
                controller: 'InstanceSPICEController',
                backdrop: "static",
                size: 'lg',
                scope: $scope,
                resolve: {
                    'spice_console': function (CommonHttpService) {
                        return CommonHttpService.post("/api/instances/" + ins.id + "/action/", post_data);
                    }
                }
            });
        };

        var action_func = {
            "novnc_console": instance_novnc_console,
            "vnc_console": instance_vnc_console,
            "spice_console": instance_spice_console
        };

        $scope.instance_action = function (ins, action) {
            action_func[action](ins);
        };



        $scope.instancemanages = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.instancemanages);

        $scope.instancemanage_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    Instancemanage.query(function(data){
                        $scope.instancemanages = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.instancemanages);
                    });
                }
            });


        var delete_Instancemanages = function(ids){

            $ngBootbox.confirm($i18next("instancemanage.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/instancemanage/delete_instance/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.instancemanage_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };



        var deleteInstancemanages = function(ids){

            $ngBootbox.confirm($i18next("instancemanage.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/instancemanage/devicepolicy/undo/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.instancemanage_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.batchDelete = function(){

            delete_Instancemanages(function(){
                var ids = [];

                checkboxGroup.forEachChecked(function(instancemanage){
                    if(instancemanage.checked){
                        ids.push(instancemanage.id);
                    }
                });

                return ids;
            });
        };

        $scope.delete = function(instancemanage){
            deleteInstancemanages([instancemanage.id]);
        };


        $scope.delete_instance = function(instancemanage){
            delete_Instancemanages([instancemanage.id]);
        };


        $scope.edit = function(instancemanage){

            $modal.open({
                templateUrl: 'update.html',
                controller: 'InstancemanageUpdateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    instancemanage_table: function () {
                        return $scope.instancemanage_table;
                    },
                    instancemanage: function(){return instancemanage},
                    AssignRoles: function(){
                        return CommonHttpService.get('/api/instancemanage/devicepolicy/');
                    }
                }
            });
        };

        $scope.openNewInstancemanageModal = function(){
            $modal.open({
                templateUrl: 'new-instancemanage.html',
                backdrop: "static",
                controller: 'NewInstancemanageController',
                size: 'lg',
                resolve: {
                    dataCenters: function(){
                        return DataCenter.query().$promise;
                    }
                }
            }).result.then(function(){
                $scope.instancemanage_table.reload();
            });
        };
    })


    .controller('NewInstancemanageController',
        function($scope, $modalInstance, $i18next,
                 CommonHttpService, ToastrService, InstancemanageForm, dataCenters){

            var form = null;
            $modalInstance.rendered.then(function(){
                form = InstancemanageForm.init($scope.site_config.WORKFLOW_ENABLED);
            });

            $scope.dataCenters = dataCenters;
            $scope.instancemanage = {is_resource_user: false, is_approver: false};
            $scope.is_submitting = false;
            $scope.cancel = $modalInstance.dismiss;
            $scope.create = function(){

                if(form.valid() == false){
                    return;
                }

                $scope.is_submitting = true;
                CommonHttpService.post('/api/instancemanage/create/', $scope.instancemanage).then(function(result){
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

   ).factory('InstancemanageForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            instancemanagename: {
                                required: true,
                                remote: {
                                    url: "/api/instancemanage/is-name-unique/",
                                    data: {
                                        instancemanagename: $("#instancemanagename").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            instancemanagename: {
                                remote: $i18next('instancemanage.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#instancemanageForm', config);
                }
            }
        }]).controller('InstancemanageUpdateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 instancemanage, instancemanage_table, CheckboxGroup,
                 Instancemanage, UserDataCenter, instancemanageForm, AssignRoles,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.instancemanage = instancemanage = angular.copy(instancemanage);
            $scope.roles = roles = AssignRoles;
            var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.roles);
            $scope.cancel = $modalInstance.dismiss;

            $modalInstance.rendered.then(instancemanageForm.init);


            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            $modalInstance.rendered.then(function(){
                form = instancemanageForm.init($scope.site_config.WORKFLOW_ENABLED);
            });
            $scope.submit = function(instancemanage){

                var params_data = {"id": instancemanage.id}
                if(!$("#InstancemanageForm").validate().form()){
                    return;
                }

                var return_roles = function(){

                    var ids = [];
                    var count = 0;
                    checkboxGroup.forEachChecked(function(roles){
                        if(roles.checked){
                                ids.push(roles.name);
                            }
                    });
                    if(count == roles.length){
                        ids = "all"
                    }
                    //alert(ids)
                                        return ids;
                                                            };


                params_data.role = return_roles
 
                CommonHttpService.post("/api/instancemanage/devicepolicy/update/", params_data).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        instancemanage_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   ).factory('instancemanageForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            instancemanagename: {
                                required: true,
                                remote: {
                                    url: "/api/instancemanage/is-name-unique/",
                                    data: {
                                        instancemanagename: $("#instancemanagename").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            instancemanagename: {
                                remote: $i18next('instancemanage.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#InstancemanageForm', config);
                }
            }
        }])    .controller('InstanceNOVNCController', function ($rootScope, $scope, $sce,
                                                   $modalInstance, novnc_console) {
        $scope.novnc_console = novnc_console;
        $scope.novnc_sce_url = function (novnc_console) {
            return $sce.trustAsResourceUrl(novnc_console.novnc_url);
        };

        $scope.cancel = function () {
            $modalInstance.dismiss();
        };
    })


    .controller('InstanceVNCController', function ($rootScope, $scope, $sce,
                                                   $modalInstance, vnc_console) {
        $scope.vnc_console = vnc_console;
        $scope.vnc_sce_url = function (vnc_console) {
            return $sce.trustAsResourceUrl(vnc_console.vnc_url);
        };

        $scope.cancel = function () {
            $modalInstance.dismiss();
        };
    })


    .controller('InstanceSPICEController', function ($rootScope, $location,$scope, $sce,
                                                   $modalInstance, spice_console) {
        $scope.spice_console = spice_console;
        $scope.spice_sce_url = function (spice_console) {
            return $sce.trustAsResourceUrl(spice_console.spice_url);
        };



        $scope.cancel = function () {
            $modalInstance.dismiss();
        };
    });
