<template>
  <div class="kb-detail">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="kb-name">{{ knowledgeBase.name }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 左侧：知识库信息和检索测试 -->
      <el-col :span="8">
        <!-- 知识库信息 -->
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px">
              <el-icon><Document /></el-icon>
              <span style="font-weight: 600">知识库信息</span>
            </div>
          </template>

          <el-descriptions :column="1" border size="default">
            <el-descriptions-item label="名称">
              <span style="font-weight: 500">{{ knowledgeBase.name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="作用域">
              <el-tag :type="getScopeTagType(knowledgeBase.scope_type)" size="default">
                {{ getScopeLabel(knowledgeBase.scope_type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文档数">
              <el-tag type="primary" size="default">{{ knowledgeBase.document_count || 0 }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文本块数">
              <el-tag type="success" size="default">{{ knowledgeBase.chunk_count || 0 }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总大小">
              <span style="color: var(--el-text-color-regular)">{{ formatSize(knowledgeBase.total_size) }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="创建者">
              <span style="color: var(--el-text-color-regular)">{{ knowledgeBase.owner_name }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              <span style="color: var(--el-text-color-regular)">{{ formatTime(knowledgeBase.created_at) }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 向量检索测试 -->
        <el-card shadow="hover" style="margin-top: 20px">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-icon><Search /></el-icon>
                <span style="font-weight: 600">向量检索测试</span>
              </div>
              <el-tag type="info" size="small" effect="plain">测试知识库效果</el-tag>
            </div>
          </template>

          <div>
            <el-input
              v-model="searchQuery"
              type="textarea"
              :rows="3"
              placeholder="输入查询内容，测试向量检索效果..."
              :disabled="searching"
            />
            
            <div style="margin-top: 15px">
              <!-- 相似度阈值设置 -->
              <div style="margin-bottom: 15px; padding: 12px; background: var(--el-fill-color-lighter); border-radius: 6px">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px">
                  <span style="font-size: 13px; color: var(--el-text-color-regular); font-weight: 500">相似度阈值:</span>
                  <el-slider
                    v-model="searchSimilarityThreshold"
                    :min="0.3"
                    :max="1.0"
                    :step="0.05"
                    :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`"
                    style="flex: 1"
                    @change="saveSimilarityThreshold"
                  />
                  <span style="font-size: 14px; color: var(--el-color-primary); font-weight: 600; min-width: 45px; text-align: right">
                    {{ (searchSimilarityThreshold * 100).toFixed(0) }}%
                  </span>
                  <el-popover placement="top" width="250" trigger="hover">
                    <template #reference>
                      <el-icon style="cursor: help; color: var(--el-text-color-secondary); font-size: 16px">
                        <QuestionFilled />
                      </el-icon>
                    </template>
                    <div style="font-size: 12px; line-height: 1.8">
                      <p style="margin: 0 0 8px 0; font-weight: 600">相似度阈值说明：</p>
                      <p style="margin: 4px 0">• 80-100%：极高相关（严格）</p>
                      <p style="margin: 4px 0">• 70-80%：高相关（推荐）</p>
                      <p style="margin: 4px 0">• 60-70%：中等相关</p>
                      <p style="margin: 4px 0">• 50-60%：低相关（宽松）</p>
                      <p style="margin: 4px 0">• &lt;50%：不推荐</p>
                    </div>
                  </el-popover>
                </div>
              </div>
              
              <!-- 检索参数和按钮 -->
              <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px">
                <el-select v-model="searchTopK" size="default" style="width: 130px">
                  <el-option label="返回 3 条" :value="3" />
                  <el-option label="返回 5 条" :value="5" />
                  <el-option label="返回 10 条" :value="10" />
                  <el-option label="返回 20 条" :value="20" />
                </el-select>
                
                <el-button 
                  type="primary" 
                  :loading="searching" 
                  @click="handleSearch"
                  :disabled="!searchQuery.trim()"
                  style="flex: 1"
                >
                  <el-icon v-if="!searching" style="margin-right: 4px"><Search /></el-icon>
                  {{ searching ? '检索中...' : '开始检索' }}
                </el-button>
              </div>
            </div>

            <!-- 检索结果 -->
            <div v-if="searchResults.length > 0" style="margin-top: 20px">
              <el-divider>
                <el-tag type="success">
                  找到 {{ searchResults.length }} 个相关结果
                </el-tag>
              </el-divider>

              <div 
                v-for="(result, index) in searchResults" 
                :key="result.chunk_id"
                style="margin-bottom: 15px"
              >
                <el-card shadow="hover" :body-style="{ padding: '15px' }">
                  <template #header>
                    <div style="display: flex; justify-content: space-between; align-items: center">
                      <div>
                        <el-tag size="small" type="primary">
                          #{{ index + 1 }}
                        </el-tag>
                        <span style="margin-left: 10px; font-size: 14px">
                          {{ result.document?.title || '未命名文档' }}
                        </span>
                      </div>
                      <el-tag 
                        :type="result.similarity > 0.8 ? 'success' : result.similarity > 0.6 ? 'warning' : 'info'"
                        size="small"
                      >
                        相似度: {{ result.similarity_percent }}
                      </el-tag>
                    </div>
                  </template>

                  <div>
                    <el-text 
                      line-clamp="4" 
                      style="font-size: 13px; color: #606266"
                    >
                      {{ result.content }}
                    </el-text>
                    
                    <div style="margin-top: 10px; font-size: 12px; color: #909399">
                      <el-space :size="15">
                        <span>
                          <el-icon><Document /></el-icon>
                          块 #{{ result.chunk_index }}
                        </span>
                        <span>
                          <el-icon><EditPen /></el-icon>
                          {{ result.char_count }} 字符
                        </span>
                        <span>
                          <el-icon><Coin /></el-icon>
                          {{ result.token_count }} tokens
                        </span>
                      </el-space>
                    </div>
                  </div>
                </el-card>
              </div>
            </div>

            <!-- 空状态提示 -->
            <el-empty 
              v-else-if="hasSearched && searchResults.length === 0"
              description="未找到相关内容"
              :image-size="80"
            >
              <template #extra>
                <el-text type="info" size="small">
                  尝试使用不同的关键词或上传更多文档
                </el-text>
              </template>
            </el-empty>

            <!-- 初始提示 -->
            <div v-else style="margin-top: 20px; text-align: center; color: #909399; font-size: 13px">
              <el-icon size="40" color="#C0C4CC"><Search /></el-icon>
              <div style="margin-top: 10px">
                输入查询内容并点击"开始检索"按钮<br>
                测试知识库的向量检索效果
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：文档列表 -->
      <el-col :span="18">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>文档列表</span>
              <el-button type="primary" @click="showUploadDialog = true">
                <el-icon><Upload /></el-icon>
                上传文档
              </el-button>
            </div>
          </template>

          <!-- 文档列表 -->
          <el-table v-loading="loading" :data="documents" stripe>
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="file_type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.file_type.toUpperCase() }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" label="大小" width="100">
              <template #default="{ row }">
                {{ formatSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="embedding_status" label="向量化状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.embedding_status)" size="small">
                  {{ getStatusLabel(row.embedding_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" label="文本块" width="80" />
            <el-table-column prop="created_at" label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="viewDocument(row)">
                  查看
                </el-button>
                <el-button 
                  v-if="row.embedding_status === 'pending' || row.embedding_status === 'failed'"
                  size="small" 
                  type="success" 
                  link 
                  @click="handleTriggerEmbedding(row)"
                >
                  向量化
                </el-button>
                <el-button size="small" type="danger" link @click="confirmDeleteDoc(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next"
            @size-change="loadDocuments"
            @current-change="loadDocuments"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 文档详情对话框 -->
    <el-dialog 
      v-model="showChunksDialog" 
      :title="`文档详情 - ${currentDocument?.title || ''}`" 
      width="80%"
      top="5vh"
    >
      <div v-if="currentDocument">
        <!-- 文档基本信息 -->
        <el-descriptions :column="3" border style="margin-bottom: 20px">
          <el-descriptions-item label="文件类型">
            <el-tag size="small">{{ currentDocument.file_type?.toUpperCase() }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatSize(currentDocument.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="向量化状态">
            <el-tag :type="getStatusType(currentDocument.embedding_status)" size="small">
              {{ getStatusLabel(currentDocument.embedding_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文本块数量">
            {{ currentDocument.chunk_count || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">
            {{ formatTime(currentDocument.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="向量化时间">
            {{ currentDocument.embedded_at ? formatTime(currentDocument.embedded_at) : '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 文本块列表 -->
        <div v-if="currentDocument.embedding_status === 'completed' && currentDocument.chunk_count > 0">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
            <h3>文本块列表</h3>
            <el-tag type="info">共 {{ documentChunks.length }} 个文本块</el-tag>
          </div>
          
          <el-table 
            v-loading="chunksLoading" 
            :data="documentChunks" 
            stripe 
            max-height="500"
            style="width: 100%"
          >
            <el-table-column prop="chunk_index" label="序号" width="80" />
            <el-table-column label="内容预览" min-width="300">
              <template #default="{ row }">
                <el-text line-clamp="2">{{ row.content }}</el-text>
              </template>
            </el-table-column>
            <el-table-column prop="char_count" label="字符数" width="100" />
            <el-table-column prop="token_count" label="Token数" width="100" />
            <el-table-column label="向量状态" width="120">
              <template #default="{ row }">
                <el-tag 
                  :type="row.has_embedding ? 'success' : 'danger'" 
                  size="small"
                >
                  {{ row.has_embedding ? '✅ 已向量化' : '❌ 无向量' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  type="primary" 
                  link 
                  @click="showChunkDetail(row)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 未向量化提示 -->
        <el-empty 
          v-else-if="currentDocument.embedding_status === 'pending'"
          description="文档尚未向量化，请点击'向量化'按钮进行处理"
        />
        
        <el-empty 
          v-else-if="currentDocument.embedding_status === 'failed'"
          description="文档向量化失败"
        >
          <template #extra>
            <el-button type="primary" @click="handleTriggerEmbedding(currentDocument)">
              重新向量化
            </el-button>
          </template>
        </el-empty>

        <el-empty 
          v-else-if="currentDocument.embedding_status === 'processing'"
          description="文档正在向量化处理中，请稍后..."
        />
      </div>

      <template #footer>
        <el-button @click="showChunksDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="600px">
      <el-form :model="uploadForm" label-width="120px">
        <el-form-item label="选择文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :accept="'.txt,.md'"
            :on-change="handleFileChange"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                只支持 TXT 和 Markdown 格式，文件大小不超过 1MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="标题">
          <el-input v-model="uploadForm.title" placeholder="留空则使用文件名" />
        </el-form-item>

        <el-form-item label="切分方式">
          <el-select v-model="uploadForm.split_mode" placeholder="选择切分方式" style="width: 100%">
            <el-option label="固定大小（推荐）" value="fixed">
              <span>固定大小</span>
              <span style="color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px">
                适合大部分文档
              </span>
            </el-option>
            <el-option label="按段落切分（单换行）" value="paragraph">
              <span>按段落切分（单换行）</span>
              <span style="color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px">
                以单换行为分隔符
              </span>
            </el-option>
            <el-option label="按段落切分（双换行）" value="paragraph_double">
              <span>按段落切分（双换行）</span>
              <span style="color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px">
                以双换行为分隔符
              </span>
            </el-option>
            <el-option label="按句子切分" value="sentence">
              <span>按句子切分</span>
              <span style="color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px">
                适合短文本
              </span>
            </el-option>
            <el-option label="自定义大小" value="custom">
              <span>自定义大小</span>
              <span style="color: var(--el-text-color-secondary); font-size: 12px; margin-left: 10px">
                手动设置参数
              </span>
            </el-option>
          </el-select>
          <div style="margin-top: 5px; font-size: 12px; color: var(--el-text-color-secondary)">
            💡 提示：切分方式会影响检索效果，建议使用默认方式
          </div>
        </el-form-item>

        <!-- 自定义切分参数 -->
        <template v-if="uploadForm.split_mode === 'custom'">
          <el-form-item label="文本块大小">
            <el-input-number 
              v-model="uploadForm.chunk_size" 
              :min="100" 
              :max="2000" 
              :step="50"
              style="width: 100%"
            />
            <div style="margin-top: 5px; font-size: 12px; color: var(--el-text-color-secondary)">
              字符数，建议 300-600
            </div>
          </el-form-item>

          <el-form-item label="重叠大小">
            <el-input-number 
              v-model="uploadForm.chunk_overlap" 
              :min="0" 
              :max="200" 
              :step="10"
              style="width: 100%"
            />
            <div style="margin-top: 5px; font-size: 12px; color: var(--el-text-color-secondary)">
              字符数，建议 50-100
            </div>
          </el-form-item>
        </template>

        <!-- 参数说明 -->
        <el-form-item v-if="uploadForm.split_mode !== 'custom'">
          <el-alert type="info" :closable="false" show-icon>
            <template #title>
              <div style="font-size: 12px">
                <div v-if="uploadForm.split_mode === 'fixed'">
                  <strong>固定大小切分：</strong>按照固定字符数切分（500字符/块，重叠50字符）
                </div>
                <div v-else-if="uploadForm.split_mode === 'paragraph'">
                  <strong>按段落切分（单换行）：</strong>以单换行符（\n）为分隔符切分，保持段落完整性
                </div>
                <div v-else-if="uploadForm.split_mode === 'paragraph_double'">
                  <strong>按段落切分（双换行）：</strong>以双换行符（\n\n）为分隔符切分，保持段落完整性
                </div>
                <div v-else-if="uploadForm.split_mode === 'sentence'">
                  <strong>按句子切分：</strong>在句子边界处切分，适合问答场景
                </div>
              </div>
            </template>
          </el-alert>
        </el-form-item>

        <el-form-item label="自动向量化">
          <el-switch v-model="uploadForm.auto_embedding" />
          <span style="margin-left: 10px; font-size: 12px; color: var(--el-text-color-secondary)">
            开启后会自动进行向量化处理
          </span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="info" :loading="previewing" @click="handlePreview">
          <el-icon><View /></el-icon>
          预览切分
        </el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          <el-icon><Upload /></el-icon>
          直接上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 切分预览对话框 -->
    <el-dialog 
      v-model="showPreviewDialog" 
      title="文档切分预览" 
      width="80%"
      top="5vh"
    >
      <div v-if="previewData">
        <!-- 预览摘要 -->
        <el-alert type="info" :closable="false" style="margin-bottom: 20px">
          <template #title>
            <div style="font-size: 14px">
              <strong>切分结果摘要</strong>
              <div style="margin-top: 10px; font-size: 13px; color: var(--el-text-color-regular)">
                文件名：{{ previewData.file_name }} | 
                大小：{{ formatSize(previewData.file_size) }} | 
                文本块数：{{ previewData.total_chunks }} 个 | 
                切分方式：{{ getSplitModeLabel(previewData.split_config?.split_mode) }}
              </div>
            </div>
          </template>
        </el-alert>

        <!-- 编码警告 -->
        <el-alert 
          v-if="previewData.file_encoding && previewData.file_encoding.toLowerCase() !== 'utf-8'"
          type="warning" 
          :closable="false"
          style="margin-bottom: 15px"
        >
          <template #title>
            ⚠️ 检测到非 UTF-8 编码
          </template>
          <div style="font-size: 13px">
            当前文件编码为 <strong>{{ previewData.file_encoding.toUpperCase() }}</strong>，
            建议使用 UTF-8 编码保存文件以获得最佳兼容性。
            <div style="margin-top: 8px">
              <el-link type="primary" :underline="false" href="https://www.baidu.com/s?wd=如何将文件转换为UTF8编码" target="_blank">
                <el-icon><QuestionFilled /></el-icon>
                如何转换为 UTF-8？
              </el-link>
            </div>
          </div>
        </el-alert>

        <!-- 文件信息和编码 -->
        <el-descriptions :column="2" border size="small" style="margin-bottom: 15px">
          <el-descriptions-item label="文件编码">
            <el-tag :type="getEncodingTagType(previewData.file_encoding)" size="small">
              {{ previewData.file_encoding?.toUpperCase() || 'UTF-8' }}
            </el-tag>
            <span style="margin-left: 8px; color: var(--el-text-color-secondary); font-size: 12px">
              置信度: {{ previewData.encoding_confidence || '99%' }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="内容统计" v-if="previewData.content_stats">
            总字符: {{ previewData.content_stats.total_chars }} | 
            中文: {{ previewData.content_stats.chinese_chars }} | 
            英文: {{ previewData.content_stats.english_chars }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 切分参数 -->
        <el-descriptions :column="3" border size="small" style="margin-bottom: 20px">
          <el-descriptions-item label="切分方式">
            {{ getSplitModeLabel(previewData.split_config?.split_mode) }}
          </el-descriptions-item>
          <el-descriptions-item label="块大小">
            {{ previewData.split_config?.chunk_size || '默认' }} 字符
          </el-descriptions-item>
          <el-descriptions-item label="重叠大小">
            {{ previewData.split_config?.chunk_overlap || '默认' }} 字符
          </el-descriptions-item>
        </el-descriptions>

        <!-- 文本块预览 -->
        <div style="margin-bottom: 10px">
          <h3 style="display: inline-block">文本块预览</h3>
          <el-tag type="warning" style="margin-left: 10px">
            显示前 {{ previewData.preview_chunks?.length }} 个（共 {{ previewData.total_chunks }} 个）
          </el-tag>
        </div>

        <el-table 
          :data="previewData.preview_chunks" 
          stripe 
          max-height="400"
          style="width: 100%"
        >
          <el-table-column prop="chunk_index" label="序号" width="80" />
          <el-table-column label="内容预览" min-width="400">
            <template #default="{ row }">
              <el-text line-clamp="3">{{ row.content_preview }}</el-text>
            </template>
          </el-table-column>
          <el-table-column prop="char_count" label="字符数" width="100" />
          <el-table-column prop="token_count" label="Token数" width="100" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button 
                size="small" 
                type="primary" 
                link 
                @click="showPreviewChunkDetail(row)"
              >
                查看全文
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 提示信息 -->
        <el-alert 
          v-if="previewData.total_chunks > 100" 
          type="warning" 
          :closable="false"
          style="margin-top: 15px"
        >
          <template #title>
            ⚠️ 文档较大，包含 {{ previewData.total_chunks }} 个文本块，向量化可能需要较长时间
          </template>
        </el-alert>

        <el-alert 
          v-if="previewData.total_chunks > 200" 
          type="error" 
          :closable="false"
          style="margin-top: 10px"
        >
          <template #title>
            🚨 文本块过多！建议：
            <ul style="margin: 10px 0 0 20px">
              <li>增大块大小（使用自定义模式，设置为 800-1000 字符）</li>
              <li>或拆分成多个文档分别上传</li>
            </ul>
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="cancelPreview">
          <el-icon><Back /></el-icon>
          返回修改
        </el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          <el-icon><Check /></el-icon>
          确认上传并向量化
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, View, Check, Back, QuestionFilled, Search, Document, EditPen, Coin } from '@element-plus/icons-vue'
import {
  getKnowledgeBase,
  getDocuments,
  uploadDocument,
  deleteDocument,
  triggerEmbedding,
  getDocumentChunks,
  previewDocumentChunks,
  searchInKnowledgeBase,
  updateKnowledgeBase
} from '@/api/knowledgeBases'

const route = useRoute()
const router = useRouter()

// 数据
const loading = ref(false)
const uploading = ref(false)
const previewing = ref(false)
const showUploadDialog = ref(false)
const showPreviewDialog = ref(false)
const showChunksDialog = ref(false)
const knowledgeBase = ref({})
const documents = ref([])
const selectedFile = ref(null)
const currentDocument = ref(null)
const documentChunks = ref([])
const chunksLoading = ref(false)
const previewData = ref(null)

// 向量检索相关
const searchQuery = ref('')
const searchTopK = ref(5)
const searchSimilarityThreshold = ref(0.7)  // 相似度阈值，默认0.7
const searchResults = ref([])
const searching = ref(false)
const hasSearched = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const uploadForm = reactive({
  title: '',
  auto_embedding: true,
  split_mode: 'fixed',  // 默认固定大小
  chunk_size: 500,      // 自定义模式下的块大小
  chunk_overlap: 50     // 自定义模式下的重叠大小
})

// 方法
const loadKnowledgeBase = async () => {
  try {
    const response = await getKnowledgeBase(route.params.uuid)
    const data = response.data || response
    knowledgeBase.value = data
    
    // 从知识库配置中加载相似度阈值
    if (data.retrieval_config && data.retrieval_config.similarity_threshold !== undefined) {
      searchSimilarityThreshold.value = parseFloat(data.retrieval_config.similarity_threshold)
    }
  } catch (error) {
    ElMessage.error('加载知识库信息失败')
  }
}

// 保存相似度阈值到知识库配置
const saveSimilarityThreshold = async () => {
  try {
    const retrievalConfig = {
      ...(knowledgeBase.value.retrieval_config || {}),
      similarity_threshold: searchSimilarityThreshold.value
    }
    
    await updateKnowledgeBase(route.params.uuid, {
      retrieval_config: retrievalConfig
    })
    
    // 更新本地知识库数据
    knowledgeBase.value.retrieval_config = retrievalConfig
  } catch (error) {
    console.error('保存相似度阈值失败:', error)
    // 不显示错误提示，避免干扰用户操作
  }
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    const response = await getDocuments(route.params.uuid, params)
    const data = response.data || response

    documents.value = data.documents || []
    pagination.total = data.total || 0
  } catch (error) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

const getScopeTagType = (scopeType) => {
  const typeMap = {
    system: 'danger',
    school: 'warning',
    course: 'success',
    agent: 'info'
  }
  return typeMap[scopeType] || 'info'
}

const getScopeLabel = (scopeType) => {
  const labelMap = {
    system: '系统',
    school: '学校',
    course: '课程',
    agent: '智能体'
  }
  return labelMap[scopeType] || scopeType
}

const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status) => {
  const labelMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return labelMap[status] || status
}

const formatSize = (bytes) => {
  if (!bytes) return '0B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + sizes[i]
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const handleFileChange = (file) => {
  // 检查文件大小（1MB = 1048576 bytes）
  const MAX_SIZE = 1 * 1024 * 1024
  
  if (file.size > MAX_SIZE) {
    ElMessage.error(`文件大小超过限制，最大支持 1MB（当前文件：${(file.size / 1024 / 1024).toFixed(2)}MB）`)
    return false
  }
  
  selectedFile.value = file.raw
  if (!uploadForm.title) {
    uploadForm.title = file.name
  }
}

const handlePreview = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  previewing.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('split_mode', uploadForm.split_mode)
    
    // 如果是自定义模式，添加切分参数
    if (uploadForm.split_mode === 'custom') {
      formData.append('chunk_size', uploadForm.chunk_size)
      formData.append('chunk_overlap', uploadForm.chunk_overlap)
    }

    const res = await previewDocumentChunks(route.params.uuid, formData)
    previewData.value = res.data
    
    // 关闭上传对话框，打开预览对话框
    showUploadDialog.value = false
    showPreviewDialog.value = true
    
  } catch (error) {
    ElMessage.error('预览失败：' + (error.response?.data?.message || error.message))
  } finally {
    previewing.value = false
  }
}

const confirmUpload = async () => {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('title', uploadForm.title || selectedFile.value.name)
    formData.append('auto_embedding', uploadForm.auto_embedding)
    formData.append('split_mode', uploadForm.split_mode)
    
    // 如果是自定义模式，添加切分参数
    if (uploadForm.split_mode === 'custom') {
      formData.append('chunk_size', uploadForm.chunk_size)
      formData.append('chunk_overlap', uploadForm.chunk_overlap)
    }

    await uploadDocument(route.params.uuid, formData)

    ElMessage.success('上传成功，向量化任务已提交')
    // 关闭所有对话框
    showUploadDialog.value = false
    showPreviewDialog.value = false
    // 重置表单
    selectedFile.value = null
    uploadForm.title = ''
    uploadForm.split_mode = 'fixed'
    uploadForm.chunk_size = 500
    uploadForm.chunk_overlap = 50
    previewData.value = null
    // 刷新数据
    loadDocuments()
    loadKnowledgeBase()
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.message || error.message))
  } finally {
    uploading.value = false
  }
}

const cancelPreview = () => {
  showPreviewDialog.value = false
  showUploadDialog.value = true  // 返回上传对话框
}

const viewDocument = async (doc) => {
  // 先显示列表中的数据
  currentDocument.value = doc
  showChunksDialog.value = true
  
  // 重新获取完整的文档信息（确保包含最新的向量化完成时间）
  try {
    const res = await getDocument(route.params.uuid, doc.uuid, false)
    if (res.data) {
      currentDocument.value = res.data
    }
  } catch (error) {
    console.error('获取文档详情失败:', error)
    // 如果获取失败，继续使用列表中的数据
  }
  
  // 加载文档的文本块
  if (currentDocument.value.embedding_status === 'completed' && currentDocument.value.chunk_count > 0) {
    await loadDocumentChunks(currentDocument.value)
  } else {
    documentChunks.value = []
  }
}

const loadDocumentChunks = async (doc) => {
  chunksLoading.value = true
  try {
    const res = await getDocumentChunks(route.params.uuid, doc.uuid, {
      page: 1,
      page_size: 100  // 获取所有文本块
    })
    documentChunks.value = res.data.items || []
  } catch (error) {
    ElMessage.error('加载文本块失败')
    documentChunks.value = []
  } finally {
    chunksLoading.value = false
  }
}

const handleTriggerEmbedding = async (doc) => {
  try {
    await ElMessageBox.confirm(
      `确定要对文档"${doc.title}"进行向量化处理吗？`, 
      '确认向量化', 
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    await triggerEmbedding(route.params.uuid, doc.uuid, false)
    ElMessage.success('向量化任务已提交，请稍后刷新查看状态')
    
    // 3秒后自动刷新列表
    setTimeout(() => {
      loadDocuments()
    }, 3000)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('提交向量化任务失败')
    }
  }
}

const confirmDeleteDoc = (doc) => {
  ElMessageBox.confirm(`确定要删除文档"${doc.title}"吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteDocument(route.params.uuid, doc.uuid)
      ElMessage.success('删除成功')
      loadDocuments()
      loadKnowledgeBase()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const showChunkDetail = (chunk) => {
  ElMessageBox.alert(chunk.content, `文本块 #${chunk.chunk_index} 详情`, {
    confirmButtonText: '关闭',
    customClass: 'chunk-detail-dialog',
    dangerouslyUseHTMLString: false
  })
}

const showPreviewChunkDetail = (chunk) => {
  ElMessageBox.alert(chunk.content, `预览：文本块 #${chunk.chunk_index}`, {
    confirmButtonText: '关闭',
    customClass: 'chunk-detail-dialog',
    dangerouslyUseHTMLString: false
  })
}

const getSplitModeLabel = (mode) => {
  const labels = {
    'fixed': '固定大小',
    'paragraph': '按段落（单换行）',
    'paragraph_double': '按段落（双换行）',
    'sentence': '按句子',
    'custom': '自定义大小'
  }
  return labels[mode] || mode
}

const getEncodingTagType = (encoding) => {
  if (!encoding) return 'success'
  const enc = encoding.toLowerCase()
  if (enc === 'utf-8' || enc === 'utf8') return 'success'
  if (enc === 'gbk' || enc === 'gb2312' || enc === 'gb18030') return 'warning'
  return 'info'
}

const goBack = () => {
  router.back()
}

// 向量检索
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }

  if (knowledgeBase.value.chunk_count === 0) {
    ElMessage.warning('知识库中暂无已向量化的内容，请先上传并向量化文档')
    return
  }

  searching.value = true
  searchResults.value = []
  hasSearched.value = true

  try {
    const res = await searchInKnowledgeBase(route.params.uuid, {
      query: searchQuery.value,
      top_k: searchTopK.value,
      similarity_threshold: searchSimilarityThreshold.value  // 使用用户配置的阈值
    })

    if (res.data.results && res.data.results.length > 0) {
      searchResults.value = res.data.results
      ElMessage.success(`检索成功！共搜索 ${res.data.searched_chunks} 个文本块，找到 ${res.data.total} 个相关结果`)
    } else {
      searchResults.value = []
      ElMessage.info(res.data.message || '未找到相关内容')
    }
  } catch (error) {
    console.error('检索失败:', error)
    ElMessage.error(error.response?.data?.message || '检索失败，请稍后重试')
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

onMounted(() => {
  loadKnowledgeBase()
  loadDocuments()
})
</script>

<style scoped>
.kb-detail {
  padding: 20px;
}

.kb-name {
  font-size: 20px;
  font-weight: bold;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

:deep(.chunk-detail-dialog) {
  width: 70%;
  max-width: 800px;
}

:deep(.chunk-detail-dialog .el-message-box__message) {
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Courier New', monospace;
  line-height: 1.6;
}
</style>

