from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import MethodType, MenuType, PermissionType, ResourceType


class User(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=20, unique=True, description="用户名称", index=True)
    nickname = fields.CharField(max_length=30, null=True, description="昵称", index=True)
    email = fields.CharField(max_length=255, null=True, unique=True, description="邮箱", index=True)
    phone = fields.CharField(max_length=20, null=True, description="电话", index=True)
    password = fields.CharField(max_length=128, null=True, description="密码")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    is_superuser = fields.BooleanField(default=False, description="是否为超级管理员", index=True)
    last_login = fields.DatetimeField(null=True, description="最后登录时间", index=True)
    roles = fields.ManyToManyField("models.Role", related_name="user_roles")
    dept_id = fields.IntField(null=True, description="部门ID", index=True)

    class Meta:
        table = "user"


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="角色名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="角色描述")

    permissions = fields.ManyToManyField("models.Permission", related_name="role_permissions")

    class Meta:
        table = "role"


class Permission(BaseModel, TimestampMixin):
    """统一权限模型"""

    name = fields.CharField(max_length=50, description="权限名称", index=True)
    code = fields.CharField(max_length=100, unique=True, description="权限代码", index=True)
    description = fields.CharField(max_length=200, null=True, description="权限描述")
    permission_type = fields.CharEnumField(PermissionType, description="权限类型", index=True)
    parent_id = fields.IntField(default=0, description="父权限ID", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    # 菜单相关字段
    menu_path = fields.CharField(max_length=100, null=True, description="菜单路径")
    menu_icon = fields.CharField(max_length=100, null=True, description="菜单图标")
    menu_component = fields.CharField(max_length=100, null=True, description="菜单组件")
    is_hidden = fields.BooleanField(default=False, description="是否隐藏菜单")

    # API相关字段
    api_path = fields.CharField(max_length=100, null=True, description="API路径")
    api_method = fields.CharEnumField(MethodType, null=True, description="API方法")

    class Meta:
        table = "permission"

    @classmethod
    def generate_permission_code(
        cls,
        permission_type: PermissionType,
        api_path: str = None,
        api_method: str = None,
        menu_path: str = None,
        name: str = None,
    ) -> str:
        """
        自动生成权限代码

        规则：
        - API权限：api.{module}.{action}.{method}
        - 菜单权限：menu.{path}
        - 模块权限：module.{name}
        """
        if permission_type == PermissionType.ACTION and api_path and api_method:
            # API权限：api.user.list.get
            path_parts = api_path.strip("/").split("/")
            # 移除 'api', 'v1' 等前缀
            clean_parts = [part for part in path_parts if part not in ["api", "v1"]]
            if len(clean_parts) >= 2:
                module = clean_parts[0]  # user, role, menu 等
                action = clean_parts[1]  # list, create, update 等
                return f"api.{module}.{action}.{api_method.lower()}"
            else:
                # 处理特殊情况
                return f"api.{'.'.join(clean_parts)}.{api_method.lower()}"

        elif permission_type in [PermissionType.FEATURE, PermissionType.ACTION] and menu_path:
            # 菜单权限：menu.users, menu.roles
            clean_path = menu_path.strip("/")
            return f"menu.{clean_path}"

        elif permission_type == PermissionType.MODULE:
            # 模块权限：module.system
            if name:
                clean_name = name.replace(" ", "").replace("管理", "").lower()
                name_map = {
                    "系统": "system",
                    "用户": "user",
                    "角色": "role",
                    "菜单": "menu",
                    "权限": "permission",
                    "api": "api",
                    "部门": "dept",
                    "审计日志": "audit",
                }
                clean_name = name_map.get(clean_name, clean_name)
                return f"module.{clean_name}"

        # 默认情况：使用时间戳确保唯一性
        import time

        return f"perm.{int(time.time())}"

    async def save(self, *args, **kwargs):
        """保存前自动生成 code"""
        if not self.code:
            self.code = self.generate_permission_code(
                permission_type=self.permission_type,
                api_path=self.api_path,
                api_method=self.api_method.value if self.api_method else None,
                menu_path=self.menu_path,
                name=self.name,
            )
        await super().save(*args, **kwargs)


class Api(BaseModel, TimestampMixin):
    path = fields.CharField(max_length=100, description="API路径", index=True)
    method = fields.CharEnumField(MethodType, description="请求方法", index=True)
    summary = fields.CharField(max_length=500, description="请求简介", index=True)
    tags = fields.CharField(max_length=100, description="API标签", index=True)

    class Meta:
        table = "api"


class Menu(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, description="菜单名称", index=True)
    remark = fields.JSONField(null=True, description="保留字段")
    menu_type = fields.CharEnumField(MenuType, null=True, description="菜单类型")
    icon = fields.CharField(max_length=100, null=True, description="菜单图标")
    path = fields.CharField(max_length=100, description="菜单路径", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, description="父菜单ID", index=True)
    is_hidden = fields.BooleanField(default=False, description="是否隐藏")
    component = fields.CharField(max_length=100, description="组件")
    keepalive = fields.BooleanField(default=True, description="存活")
    redirect = fields.CharField(max_length=100, null=True, description="重定向")

    class Meta:
        table = "menu"


class Dept(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="部门名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="备注")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, max_length=10, description="父部门ID", index=True)

    class Meta:
        table = "dept"


class DeptClosure(BaseModel, TimestampMixin):
    ancestor = fields.IntField(description="父代", index=True)
    descendant = fields.IntField(description="子代", index=True)
    level = fields.IntField(default=0, description="深度", index=True)


class AuditLog(BaseModel, TimestampMixin):
    user_id = fields.IntField(description="用户ID", index=True)
    username = fields.CharField(max_length=64, default="", description="用户名称", index=True)
    module = fields.CharField(max_length=64, default="", description="功能模块", index=True)
    summary = fields.CharField(max_length=128, default="", description="请求描述", index=True)
    method = fields.CharField(max_length=10, default="", description="请求方法", index=True)
    path = fields.CharField(max_length=255, default="", description="请求路径", index=True)
    status = fields.IntField(default=-1, description="状态码", index=True)
    response_time = fields.IntField(default=0, description="响应时间(单位ms)", index=True)
    request_args = fields.JSONField(null=True, description="请求参数")
    response_body = fields.JSONField(null=True, description="返回数据")
    ip_address = fields.CharField(max_length=64, default="", description="IP地址", index=True)
    user_agent = fields.CharField(max_length=512, default="", description="用户代理", index=True)
    operation_type = fields.CharField(max_length=32, default="", description="操作类型", index=True)
    log_level = fields.CharField(max_length=16, default="info", description="日志级别", index=True)
    is_deleted = fields.BooleanField(default=False, description="是否已删除", index=True)

    class Meta:
        table = "audit_log"
        indexes = [
            # 创建复合索引以提高查询性能
            ("created_at", "username"),
            ("created_at", "module"),
            ("created_at", "status"),
            ("created_at", "operation_type"),
            ("created_at", "log_level"),
        ]

    async def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "module": self.module,
            "summary": self.summary,
            "method": self.method,
            "path": self.path,
            "status": self.status,
            "response_time": self.response_time,
            "request_args": self.request_args,
            "response_body": self.response_body,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "operation_type": self.operation_type,
            "log_level": self.log_level,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }

    @classmethod
    async def get_logs_by_date_range(cls, start_date, end_date, **filters):
        """根据日期范围和过滤条件获取日志"""
        q = Q(created_at__range=[start_date, end_date])
        for key, value in filters.items():
            if value:
                if isinstance(value, str) and key not in ["status", "user_id", "response_time"]:
                    q &= Q(**{f"{key}__icontains": value})
                else:
                    q &= Q(**{key: value})
        return await cls.filter(q & Q(is_deleted=False)).order_by("-created_at")

    @classmethod
    async def get_logs_statistics(cls, days=7):
        """获取最近n天的日志统计信息"""
        import datetime

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days - 1)

        result = {}
        for i in range(days):
            current_date = start_date + datetime.timedelta(days=i)
            next_date = current_date + datetime.timedelta(days=1)
            count = await cls.filter(
                created_at__gte=current_date.strftime("%Y-%m-%d"),
                created_at__lt=next_date.strftime("%Y-%m-%d"),
                is_deleted=False,
            ).count()
            result[current_date.strftime("%Y-%m-%d")] = count

        return result

    @classmethod
    async def batch_delete(cls, ids):
        """批量删除日志(软删除)"""
        return await cls.filter(id__in=ids).update(is_deleted=True)
