/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('InstancemanageController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Instancemanage, CheckboxGroup, DataCenter,PriceRule){
        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });
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
        
        var need_confirm = true;
        var no_confirm = false;
        $scope.openNewTemplatemanagerModal = function () { 
           $modal.open({
                templateUrl: '/static/management/views/instance_create_wizard/instance_wizard.html?t=' + Math.random(),
                controller: 'InstanceCreateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    instance_table: function () {
                        return $scope.instance_table;
                    },
                    quota: function (CommonHttpService) {
                        return CommonHttpService.get("/api/account/quota/");
                    },
                    cpuPrices: function(){
                        return PriceRule.query({'resource_type': 'cpu'}).$promise;
                    },
                    memoryPrices: function(){
                        return PriceRule.query({'resource_type': 'memory'}).$promise;
                    },
		    instancemanage_table: function(){return $scope.instancemanage_table;},
                    deps: ['$ocLazyLoad', function ($ocLazyLoad) {
                        return $ocLazyLoad.load({
                            name: 'CloudApp',
                            insertBefore: '#ng_load_plugins_before',
                            files: [
                                '/static/assets/global/plugins/bootstrap-wizard/jquery.bootstrap.wizard.min.js',
                                '/static/cloud/scripts/create_instance_wizard.js',
                            ]
                        });
                    }]
                }
            });
        };

        var post_action = function (ins, action) {
            var post_data = {
                "action": action,
                "instance": ins.id
            };

            CommonHttpService.post("/api/instances/" + ins.id + "/action/", post_data).then(function (data) {
                if (data.OPERATION_STATUS == 1) {
                    //$scope.instance_table.reload();
                    $scope.instancemanage_table.reload();
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
	$scope.snapshot = function(instancemanage){

            $modal.open({
                templateUrl: 'snapshot.html',
                controller: 'InstancemanageSnapshotController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    instancemanage_table: function () {
                        return $scope.instancemanage_table;
                    },
                    instancemanage: function(){return instancemanage},
                }
            });
        };
	
	$scope.assign = function(instancemanage){

            $modal.open({
                templateUrl: 'assign.html',
                controller: 'InstancemanageAssignController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    instancemanage_table: function () {
                        return $scope.instancemanage_table;
                    },
		    assigned_users: function (CommonHttpService) {
                        return CommonHttpService.post("/api/instancemanage/assignedusers/", {"uuid":instancemanage.uuid});
                    },
		    unassigned_users: function (CommonHttpService) {
                        return CommonHttpService.post("/api/instancemanage/unassignedusers/", {"uuid":instancemanage.uuid});
                    },
                    instancemanage: function(){return instancemanage},
                }
            });
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
		    instancemanage_table: function () {
                        return $scope.instancemanage_table;
                    },
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
        function($scope, $modalInstance, $i18next, instancemanage_table,
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
                        instancemanage_table.reload();
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
    .controller('InstanceCreateController',
    function ($rootScope, $scope, $state, $filter, $interval, lodash,
              $modalInstance, $i18next, site_config, ngTableParams, ToastrService,
              CommonHttpService, PriceTool, Instance, Image, Flavor, Network, instancemanage_table,
              instance_table, quota, cpuPrices, memoryPrices) {

        $scope.instance_config = {
            "instance": 1,
            "pay_type": "hour",
            "pay_num": 1
        };

        $scope.month_options =  [];
        $scope.year_options =  [];

        for(var i=1; i<=10; i++){
            $scope.month_options.push({value: i, label: i + "月"});
        }

        for(var i=1; i<=5; i++){
            $scope.year_options.push({value: i, label: i + "年"});
        }

        Image.query(function (data) {
            $scope.images_list = data;
            if (data.length > 0) {
                $scope.instance_config.image = data[0];
                $scope.instance_config.select_image = data[0];
                $scope.instance_config.login_type = 'password';
            }
        });
	
	$scope.core_list = [1,2,4,8];
	$scope.thread_list = [1,2,4,8];
        Flavor.query(function (data) {
            $scope.flavors_list = data;
            if (data.length > 0) {
                var cpu_memory_list = new Object();
                var cpu_array = new Array();
                var memory_array = new Array();

                for (var i = 0; i < data.length; i++) {
                    cpu_memory_list["" + data[i].cpu] = [];

                    if (cpu_array.indexOf(data[i].cpu) == -1) {
                        cpu_array.push(data[i].cpu);
                    }

                    if (memory_array.indexOf(data[i].memory) == -1) {
                        memory_array.push(data[i].memory);
                    }
                }

                for (var i = 0; i < data.length; i++) {
                    if (cpu_memory_list["" + data[i].cpu].indexOf(data[i].memory) == -1) {
                        cpu_memory_list["" + data[i].cpu].push(data[i].memory)
                    }
                }

                if(cpu_array){
                    cpu_array.sort(function(a, b){
                        return a > b;
                    });
                }

                if(memory_array){
                    memory_array.sort(function(a, b){
                        return a > b;
                    });
                }

                $scope.cpu_list = cpu_array;
                $scope.memory_list = memory_array;

                $scope.cpu_memory_map = cpu_memory_list;

                $scope.instance_config.vcpu = cpu_array[0];
                $scope.instance_config.core = $scope.core_list[0];
                $scope.instance_config.thread = $scope.thread_list[0];
                $scope.instance_config.memory = cpu_memory_list["" + cpu_array[0]][0];
                $scope.instance_config.cpu_memory = cpu_memory_list["" + cpu_array[0]];

                $scope.cpu_click = function (cpu) {
                    $scope.instance_config.vcpu = cpu;
                    $scope.instance_config.memory = $scope.cpu_memory_map["" + cpu][0];
                    $scope.instance_config.cpu_memory = $scope.cpu_memory_map[cpu];
                };

		// core & thread control
		$scope.core_thread_map = [[1,2,4,8],[2,4,8,-1],[4,8,-1,-1],[8,-1,-1,-1]]
		$scope.core_click = function (core){
		    $scope.cx = $scope.core_list.indexOf(core)
		    $scope.cy = $scope.thread_list.indexOf($scope.instance_config.thread)
           	    if ($scope.core_thread_map[$scope.cx][$scope.cy] == -1){
                    $scope.instance_config.thread = $scope.thread_list[0];
		    $scope.cy = $scope.thread_list.indexOf($scope.instance_config.thread)
                    }
                    $scope.instance_config.vcpu = $scope.core_thread_map[$scope.cx][$scope.cy]
                    $scope.instance_config.core = core;
                    $scope.instance_config.memory = $scope.cpu_memory_map["" + $scope.instance_config.vcpu][0];
                    $scope.instance_config.cpu_memory = $scope.cpu_memory_map[$scope.instance_config.vcpu];
        	};
		$scope.thread_click = function (thread){
                    $scope.tx = $scope.core_list.indexOf($scope.instance_config.core)
                    $scope.ty = $scope.thread_list.indexOf(thread)
                    if ($scope.core_thread_map[$scope.tx][$scope.ty] == -1){
                    $scope.instance_config.core = $scope.core_list[0];
                    $scope.tx = $scope.core_list.indexOf($scope.instance_config.core)
                    }                    
		    $scope.instance_config.vcpu = $scope.core_thread_map[$scope.tx][$scope.ty]
                    $scope.instance_config.thread = thread;
                    $scope.instance_config.memory = $scope.cpu_memory_map["" + $scope.instance_config.vcpu][0];
                    $scope.instance_config.cpu_memory = $scope.cpu_memory_map[$scope.instance_config.vcpu];
                };
            }
        });
	
        Network.query(function (data) {
            $scope.network_list = data;
            if (data.length > 0) {
                $scope.instance_config.network = data[0];
            }
            else {
                $scope.instance_config.network = null;
            }
        });

        $scope.instance_counter = function (step) {
            if (typeof(step) != typeof(1)) {
                return;
            }
            var expect = $scope.instance_config.instance + step;
            if (expect < 1) {
                return;
            }

            if(expect > site_config.BATCH_INSTANCE_LIMIT){
                return;
            }

            $scope.instance_config.instance = expect;
        };

        $scope.cancel = function () {

            $modalInstance.dismiss();
        };
        $scope.submit_click = function (instance_config) {
            var post_data = {
                "name": instance_config.name,
                "cpu": instance_config.vcpu,
                "core": instance_config.core,
                "thread": instance_config.thread,
                "memory": instance_config.memory,
                "network_id": instance_config.network == null ? 0 : instance_config.network.id,
                "image": instance_config.select_image.id,
                "image_info": instance_config.select_image.id,
                "sys_disk": instance_config.select_image.disk_size,
                "password": instance_config.password,
                "instance": instance_config.instance,
                "pay_type": instance_config.pay_type,
                "pay_num": instance_config.pay_num
            };
            CommonHttpService.post("/api/instances/create/", post_data).then(function (data) {
                if (data.OPERATION_STATUS == 1) {
                    ToastrService.success(data.msg, $i18next("success"));
                    $modalInstance.dismiss();
                    instancemanage_table.reload();
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
            }).then(instancemanage_table.reload());
        };

        $scope.quota = quota;
        $scope.calcuate_resource_persent = function (resource) {
            if (quota[resource] <= 0) {
                return 0;
            }
            else {
                var current = $scope.instance_config[resource];
                if (resource != "instance")
                    current = current * $scope.instance_config.instance;
                return (quota[resource + "_used"] + current) / quota[resource] * 100;

            }
        };
        $scope.resource_persent = function (resource) {
            return $scope.calcuate_resource_persent(resource) + "%";
        };
        $scope.resource_persent_desc = function (resource) {
            var str = "";
            var current = $scope.instance_config[resource];
            if (resource != "instance")
                current = current * $scope.instance_config.instance;
            str += (quota[resource + "_used"] + current) + "/";
            if (quota[resource] <= 0) {
                str += $i18next("instance.infinite");
            }
            else {
                str += quota[resource];
            }
            return str;
        };
        $scope.check_can_submit = function () {
            if ($scope.calcuate_resource_persent("instance") > 100) {
                return true;
            }
            if ($scope.calcuate_resource_persent("vcpu") > 100) {
                return true;
            }
            if ($scope.calcuate_resource_persent("memory") > 100) {
                return true;
            }
            return false;
        };

        $scope.calculateCost = function(config){

            var cpuPrice = PriceTool.getPrice(cpuPrices, config.vcpu, config.pay_type),
                memoryPrice = PriceTool.getPrice(memoryPrices, config.memory, config.pay_type);

            var totalPrice = (cpuPrice + memoryPrice) * config.pay_num * config.instance;
            return totalPrice.toFixed(3);
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
    }).controller('InstancemanageSnapshotController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 instancemanage, instancemanage_table, CheckboxGroup,
                 Instancemanage, UserDataCenter, //instancemanageForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.instancemanage = instancemanage = angular.copy(instancemanage);
            $scope.cancel = $modalInstance.dismiss;

            //$modalInstance.rendered.then(instancemanageForm.init);


            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            //$modalInstance.rendered.then(function(){
            //    form = instancemanageForm.init($scope.site_config.WORKFLOW_ENABLED);
            //});
            $scope.submit = function(instancemanage){

                var params_data = {"id": instancemanage.id, "instance_id":instancemanage.uuid, "snap_name": $scope.snapshot.snapshotname}
                if(!$("#InstancemanageForm").validate().form()){
                    return;
                }
		
 
                CommonHttpService.post("/api/snapshot/create_instance_snapshot", params_data).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
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
        }]).controller('InstancemanageAssignController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 instancemanage, instancemanage_table, CheckboxGroup, 
		 assigned_users, unassigned_users,
                 Instancemanage, UserDataCenter, //instancemanageForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.instancemanage = instancemanage = angular.copy(instancemanage);
            $scope.cancel = $modalInstance.dismiss;

            //$modalInstance.rendered.then(instancemanageForm.init);
	    //$scope.assigned_users = CommonHttpService.post("/api/instancemanage/assignedusers/", {"uuid":$scope.instancemanage.uuid})
	    $scope.assigned_users = assigned_users;
	    $scope.unassigned_users = unassigned_users;
	    $scope.selected_users = new Object;
	    $scope.unselected_users = new Object;
            $scope.cancel = function () {
                $modalInstance.dismiss();
            };

	    $scope.add = function(selected_users){
		$scope.assigned_users.push($scope.selected_users);
		alert($scope.assigned_users)
	    };
            //var form = null;
            //$modalInstance.rendered.then(function(){
            //    form = instancemanageForm.init($scope.site_config.WORKFLOW_ENABLED);
            //});
            $scope.assigned_id = []
            $scope.submit = function(instancemanage){
		//angular.forEach($scope.assigned_users, function (data){
		//	$scope.assigned_id.push(data.id)})
		//alert($scope.selected_users)
                var params_data = {"id":instancemanage.id, "assign":$scope.selected_users.id, "unassign":$scope.unselected_users.id};
                CommonHttpService.post("/api/instancemanage/assignins/", params_data).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
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
        }]);;
