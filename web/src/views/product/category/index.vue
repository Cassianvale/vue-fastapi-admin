<template>
  <CommonPage show-footer title="商品分类列表">
    <template #action>
      <div>
        <NButton
          v-permission="'post/api/v1/category/create'"
          class="float-right mr-15"
          type="primary"
          @click="handleAdd"
        >
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建分类
        </NButton>
      </div>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="loadCategories"
    >
      <template #queryBar>
        <QueryBarItem label="分类名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入分类名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="customHandleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="categoryRules"
      >
        <NFormItem label="分类名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入分类名称" />
        </NFormItem>
        <NFormItem label="分类描述" path="description">
          <NInput v-model:value="modalForm.description" type="textarea" clearable />
        </NFormItem>
        <NFormItem label="排序" path="order">
          <NInputNumber v-model:value="modalForm.order" min="0"></NInputNumber>
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NPopconfirm, useMessage } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '商品分类' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const message = useMessage()

// 加载分类数据
const loadCategories = async (params) => {
  try {
    return await api.categories.getList(params)
  } catch (error) {
    message.error('加载分类失败')
    return { data: [] }
  }
}

// 删除分类
const deleteCategory = async (id) => {
  try {
    await api.categories.delete(id)
    message.success('删除成功')
    await $table.value?.handleSearch()
  } catch (error) {
    message.error('删除失败')
  }
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleAdd,
} = useCRUD({
  name: '商品分类',
  initForm: { name: '', description: '', order: 0 },
  doCreate: (data) => api.categories.create(data),
  doUpdate: (data) => api.categories.update(data.id, data),
  doDelete: (id) => api.categories.delete(id),
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
})

const categoryRules = {
  name: [
    {
      required: true,
      message: '请输入分类名称',
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 80,
    align: 'center',
  },
  {
    title: '分类名称',
    key: 'name',
    width: 160,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '分类描述',
    key: 'description',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '排序',
    key: 'order',
    width: 100,
    align: 'center',
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    align: 'center',
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-left: 8px;',
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'post/api/v1/category/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => deleteCategory(row.id),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    style: 'margin-left: 8px;',
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  }
                ),
                [[vPermission, 'delete/api/v1/category/delete']]
              ),
            default: () => h('div', {}, '确定删除该分类吗?'),
          }
        ),
      ]
    },
  },
]

// 自定义保存处理函数
const customHandleSave = async () => {
  try {
    // 使用原始的handleSave方法处理保存操作
    await handleSave()
    // 成功消息由useCRUD组件内部处理
  } catch (error) {
    console.error('保存商品分类错误:', error)
    
    // 直接显示错误消息
    message.error(error.message)
    
    // 重置加载状态
    modalLoading.value = false
  }
}
</script> 