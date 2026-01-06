<template>
  <div class="min-h-screen bg-black text-white flex flex-col workspace-root">
    <!-- Header -->
    <header class="h-9 flex items-center justify-between px-2.5 border-b border-white/10 bg-black">
      <div class="flex items-center gap-2">
        <div class="h-6 w-6 shrink-0">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sidian logo">
            <path d="M12 2 22 22H2z" fill="#6b21a8" />
          </svg>
        </div>
        <span class="text-[12px] font-semibold">Sidian AI</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-[10px] text-white/50">Free plan</span>
        <span class="text-white/30">·</span>
        <button class="text-[10px] text-white/70 hover:text-white transition" @click="handleUpgrade">Upgrade</button>
        <div class="h-6 w-6 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-600 border border-white/15 shadow-inner flex items-center justify-center text-[9px] font-semibold text-white">
          U
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden min-w-0 min-h-0 workspace-shell">
      <!-- Icon rail -->
      <aside class="w-12 bg-[#0b0b0b] border-r border-white/10 flex flex-col items-center py-2 space-y-1.5 overflow-visible">
        <template v-for="icon in railIcons" :key="icon.id">
          <div
            v-if="icon.id === 'timesheet'"
            class="relative group"
            @mouseenter="openTimesheetMenu"
            @mouseleave="closeTimesheetMenu"
          >
            <button
              class="relative h-8 w-8 rounded border border-transparent flex items-center justify-center text-white/60 hover:text-white hover:border-white/10 transition"
              :aria-label="icon.label"
              :class="activeRail === icon.id ? 'text-white border-white/20 bg-white/5' : ''"
              @click="handleTimesheetNav(timesheetSection)"
            >
              <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-purple-500 rounded-r" v-if="icon.id === activeRail"></span>
              <component :is="icon.component" class="w-5 h-5" />
            </button>
            <div
              v-if="timesheetMenuOpen"
              class="absolute left-full top-0 ml-3 z-20 bg-[#0f0f0f] border border-white/15 rounded-xl shadow-2xl min-w-[180px] py-1.5"
            >
              <div class="px-3 py-1.5 text-[13px] font-semibold text-white/85 border-b border-white/10">Timeline</div>
              <div class="px-2.5 py-1.5 space-y-1 border-l border-white/10 ml-2">
                <button
                  v-for="item in timesheetMenuItems"
                  :key="item.id"
                  class="w-full flex items-center gap-2 px-3 py-1.75 text-[12px] text-white/70 hover:bg-white/10 rounded-lg text-left leading-tight"
                  @click="handleTimesheetNav(item.id)"
                >
                  <span class="flex items-center justify-center w-5 h-5 text-[14px] leading-none shrink-0">{{ item.icon }}</span>
                  <span class="leading-[15px]">{{ item.label }}</span>
                </button>
              </div>
            </div>
          </div>
          <div
            v-else
            class="relative group"
            @mouseenter="showSimpleMenu(icon.id)"
            @mouseleave="hideSimpleMenu"
          >
            <button
              class="relative h-8 w-8 rounded border border-transparent flex items-center justify-center text-white/60 hover:text-white hover:border-white/10 transition"
              :aria-label="icon.label"
                :class="activeRail === icon.id ? 'text-white border-white/20 bg-white/5' : ''"
                @click="setActivePage(icon.id)"
              >
                <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-purple-500 rounded-r" v-if="icon.id === activeRail"></span>
                <component :is="icon.component" class="w-5 h-5" />
              </button>
            <div
              v-if="hoveredSimpleMenu === icon.id"
              class="absolute left-full top-0 ml-3 z-20 bg-[#0f0f0f] border border-white/15 rounded-xl shadow-2xl min-w-[180px] py-2"
              @mouseenter="showSimpleMenu(icon.id)"
              @mouseleave="hideSimpleMenu"
            >
              <div class="px-3 py-1.5 text-sm font-semibold text-white/80">{{ icon.label }}</div>
            </div>
          </div>
        </template>
        <div class="mt-auto h-9 w-9 rounded border border-white/10 bg-white/5"></div>
      </aside>

      <!-- Conversation list -->
      <aside
        v-if="activePage === 'home'"
        class="w-56 bg-[#0d0d0d] border-r border-white/10 flex flex-col relative min-w-[200px] conversation-sidebar min-h-0 overflow-y-auto custom-scroll"
        style="height: calc(100vh - 36px); max-height: calc(100vh - 36px);"
      >
        <div class="px-2.5 py-2 border-b border-white/10">
          <button
            class="w-full h-8 px-3 rounded bg-white/8 border border-white/12 text-[11px] font-semibold hover:bg-white/12 transition flex items-center gap-2"
            @click="startNewConversation"
            aria-label="Start a new agent conversation"
          >
            <span class="text-sm leading-none">+</span>
            <span class="tracking-wide">NEW AGENT</span>
          </button>
        </div>

        <div class="px-2.5 py-2.5 border-b border-white/10">
          <div class="relative">
            <input
              v-model="search"
              type="text"
              class="w-full rounded bg-white/5 border border-white/10 text-[12px] px-3 py-1.5 pl-8 placeholder-white/40 focus:outline-none focus:border-white/30"
              placeholder="Search agents..."
              aria-label="Search agents"
            />
            <svg class="absolute left-3 top-2.5 w-4 h-4 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <div class="flex-1 min-h-0 overflow-y-auto custom-scroll pr-1">
          <div
            v-for="section in filteredConversationSections"
            :key="section.title"
            class="px-2.5 py-2"
          >
            <p class="text-[10px] uppercase tracking-[0.18em] text-white/35 mb-2 font-medium">{{ section.title }}</p>
            <div class="space-y-1">
              <button
                v-for="conv in section.items"
                :key="conv.id"
                class="w-full text-left px-2.5 py-1.5 rounded bg-transparent border border-transparent hover:bg-white/5 transition group"
                :class="activeConversationId === conv.id && activePage === 'home' ? 'bg-white/5 border-white/10' : ''"
                @click="selectConversation(conv.id)"
                @contextmenu.prevent.stop="openContextMenu($event, conv.id)"
                @dblclick.stop.prevent="startRename(conv.id)"
              >
                <div v-if="renamingConversationId === conv.id" class="space-y-1">
                  <div class="relative">
                    <input
                      type="text"
                      v-model="renameDraft"
                      class="w-full bg-[#1a1a1a] border border-white/20 rounded px-2 py-1 pr-4 text-[12px] font-semibold text-white focus:outline-none focus:border-white/40"
                      :ref="el => setRenameInputRef(conv.id, el as HTMLInputElement | null)"
                      @click.stop
                      @keydown.enter.stop.prevent="confirmRename(conv.id)"
                      @keydown.esc.stop.prevent="cancelRename"
                      @blur="confirmRename(conv.id)"
                    />
                    <span class="absolute right-2 top-1/2 -translate-y-1/2 w-px h-4 bg-white animate-pulse pointer-events-none"></span>
                  </div>
                  <p class="text-[10px] text-white/55">{{ conv.time }}</p>
                </div>
                <div v-else class="space-y-0.5">
                  <p class="text-[12px] font-semibold truncate" :title="conv.title">{{ conv.title }}</p>
                  <p class="text-[10px] text-white/55">{{ conv.time }}</p>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div
          v-if="contextMenu.visible && contextMenu.convId"
          ref="contextMenuRef"
          class="absolute z-20 bg-[#111] border border-white/15 rounded-lg shadow-2xl min-w-[160px] overflow-hidden"
          :style="{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }"
        >
          <button
            class="w-full text-left px-4 py-2 text-sm text-white/85 hover:bg-white/5 border-b border-white/10"
            @click="renameConversation(contextMenu.convId)"
          >
            Rename
          </button>
          <button
            class="w-full text-left px-4 py-2 text-sm text-red-300 hover:bg-red-600/20"
            @click="openDeleteDialog(contextMenu.convId)"
          >
            Delete
          </button>
        </div>
      </aside>

      <!-- Main content -->
      <main class="flex-1 bg-black flex overflow-hidden min-w-0 workspace-main">
        <div class="flex flex-col flex-1 min-h-0 w-full max-w-4xl max-w-full mx-auto py-4 px-3 gap-4 min-w-0">
          <div class="flex items-center justify-between flex-wrap gap-3"></div>

          <div v-if="activePage === 'home'" class="flex-1 min-h-0 flex justify-center">
            <div class="h-full w-full chat-frame overflow-hidden flex flex-col">
              <template v-if="!activeChatLog.length">
                <div class="flex-1 min-h-[360px] flex flex-col items-center justify-center gap-7 text-center px-5">
                  <div class="flex flex-col items-center gap-3">
                    <div class="flex items-center gap-2 text-[11px] text-white/65">
                      <span class="px-3 py-1 rounded-full bg-white/5 border border-white/12 shadow-[0_4px_16px_rgba(0,0,0,0.35)]">Free plan</span>
                      <button class="text-white/75 hover:text-white transition" @click="handleUpgrade">Upgrade</button>
                    </div>
                    <div class="flex items-center gap-3">
                      <span class="text-lg">✺</span>
                      <p class="text-[26px] font-semibold tracking-tight text-white/90" style="font-family: 'Georgia', 'Times New Roman', serif;">
                        {{ greetingMessage }}
                      </p>
                    </div>
                  </div>
                  <div class="w-full max-w-3xl">
                    <div class="relative rounded-[14px] bg-[#1c1c1c] border border-white/12 shadow-[0_8px_22px_rgba(0,0,0,0.35)] px-4 py-3 space-y-2.5 text-left">
                      <span class="absolute top-3.5 right-3.5 h-1.5 w-1.5 rounded-full border border-[#5af2cf] shadow-[0_0_0_2px_rgba(90,242,207,0.12)]"></span>
                      <textarea
                        v-model="prompt"
                        ref="promptInput"
                        class="w-full bg-transparent border-0 focus:outline-none focus:ring-0 text-[14px] leading-[1.6] text-white placeholder-white/55 resize-none min-h-[38px] max-h-[160px] overflow-y-hidden"
                        placeholder="How can I help you today?"
                        aria-label="Prompt input"
                        rows="1"
                        @keydown.enter.exact.prevent="handleSend"
                        @input="resizePrompt"
                      ></textarea>
                      <div class="flex flex-wrap items-center justify-between gap-3 text-white/75">
                        <div class="flex flex-wrap items-center gap-2">
                          <button
                            class="h-9 w-9 rounded-full border border-white/12 bg-white/5 hover:bg-white/10 transition flex items-center justify-center"
                            aria-label="Attach"
                            @click="openFilePicker"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14m-7-7h14" />
                            </svg>
                          </button>
                          <div class="h-9 w-9 rounded-full border border-white/12 bg-white/5 flex items-center justify-center text-white/70">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l2.5 2.5" />
                              <circle cx="12" cy="12" r="8.5" stroke-width="2" />
                            </svg>
                          </div>
                          <div class="flex items-center gap-1.5">
                            <button
                              class="px-2 h-8 rounded-full border text-[11px] font-semibold transition"
                              :class="dataSources.project_db ? 'bg-purple-700 text-white border-purple-500/60' : 'bg-white/5 border-white/12 text-white/60'"
                              type="button"
                              @click="toggleDataSource('project_db')"
                            >
                              Project DB
                            </button>
                            <button
                              class="px-2 h-8 rounded-full border text-[11px] font-semibold transition"
                              :class="dataSources.code_db ? 'bg-purple-700 text-white border-purple-500/60' : 'bg-white/5 border-white/12 text-white/60'"
                              type="button"
                              @click="toggleDataSource('code_db')"
                            >
                              Code DB
                            </button>
                            <button
                              class="px-2 h-8 rounded-full border text-[11px] font-semibold transition"
                              :class="dataSources.coop_manual ? 'bg-purple-700 text-white border-purple-500/60' : 'bg-white/5 border-white/12 text-white/60'"
                              type="button"
                              @click="toggleDataSource('coop_manual')"
                            >
                              Coop Manual
                            </button>
                          </div>
                        </div>
                        <div class="flex items-center gap-3">
                          <button
                            class="px-3.5 h-9 rounded-full bg-white/5 border border-white/12 hover:bg-white/10 transition text-[12px] font-semibold flex items-center gap-1.5"
                            type="button"
                            @click="cycleModel"
                            :title="`Model: ${selectedModel}`"
                          >
                            <span class="text-white/85">{{ selectedModel }}</span>
                            <svg class="w-3 h-3 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                          <button
                            class="h-9 w-9 rounded-full flex items-center justify-center text-white flex-shrink-0 transition"
                            :class="(prompt.trim() || attachments.length) && !isSending ? 'bg-[#6b21a8] hover:bg-[#7c2cc7]' : 'bg-[#6b21a8]/50 cursor-not-allowed'"
                            aria-label="Send"
                            @click="handleSend"
                            :disabled="isSending || (!prompt.trim() && !attachments.length)"
                          >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <template v-else>
                <div class="flex-1 min-h-0 flex flex-col">
                  <div ref="chatContainer" class="flex-1 min-h-0 overflow-y-auto px-4 py-4 custom-scroll relative">
                    <div class="max-w-2xl mx-auto space-y-3">
                      <div
                        v-for="(entry, idx) in activeChatLog"
                        :key="idx"
                        class="flex gap-4"
                        :class="entry.role === 'user' ? 'justify-end' : 'justify-start'"
                      >
                        <div
                          v-if="entry.role === 'assistant'"
                          class="h-8 w-8 rounded-full bg-gradient-to-br from-purple-600 to-fuchsia-600 flex items-center justify-center text-[12px] font-semibold flex-shrink-0"
                        >
                          S
                        </div>
                        <div
                          class="max-w-[520px] rounded-2xl px-3.5 py-3 leading-relaxed shadow-lg"
                          :class="entry.role === 'user'
                            ? 'bg-[#2a2a2a] border border-white/10'
                            : 'bg-transparent'
                          "
                        >
                          <p class="text-[9px] uppercase tracking-[0.12em] text-white/40 mb-1">
                            {{ entry.role === 'user' ? 'You' : 'Sid' }}
                          </p>
                          <div v-if="entry.role === 'assistant'" class="prose prose-invert prose-sm max-w-none" v-html="entry.content"></div>
                          <div v-else class="whitespace-pre-wrap text-[12px] text-white/90">{{ entry.content }}</div>
                          <div
                            v-if="entry.attachments?.length"
                            class="flex flex-wrap gap-2 mt-3"
                          >
                            <span
                              v-for="file in entry.attachments"
                              :key="file"
                              class="px-2.5 py-1 rounded bg-white/5 border border-white/10 text-[12px] text-white/80"
                            >
                              {{ file }}
                            </span>
                          </div>
                        </div>
                        <div
                          v-if="entry.role === 'user'"
                          class="h-9 w-9 rounded-full bg-white/10 border border-white/10 flex items-center justify-center text-[11px] font-semibold flex-shrink-0"
                        >
                          You
                        </div>
                      </div>
                    </div>
                    <button
                      v-if="showScrollToBottom"
                      @click="scrollToBottom(true)"
                      class="absolute right-4 bottom-4 h-9 w-9 rounded-full bg-white/10 border border-white/20 backdrop-blur hover:bg-white/20 transition text-white flex items-center justify-center shadow-lg"
                      aria-label="Scroll to latest message"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </div>

                  <div class="px-4 py-3">
                    <div class="max-w-3xl mx-auto space-y-2.5">
                      <div v-if="attachments.length" class="flex flex-wrap gap-2">
                        <div
                          v-for="(file, idx) in attachments"
                          :key="file.name + idx"
                          class="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1f1f1f] border border-white/12 text-xs text-white/80"
                        >
                          <span class="max-w-[180px] truncate">{{ file.name }}</span>
                          <button
                            class="text-white/50 hover:text-white transition"
                            type="button"
                            @click="removeAttachment(idx)"
                            aria-label="Remove attachment"
                          >
                            ×
                          </button>
                        </div>
                      </div>

                      <div class="relative rounded-[14px] bg-[#1c1c1c] border border-white/12 shadow-[0_8px_22px_rgba(0,0,0,0.35)] px-4 py-3 space-y-2.5">
                        <span class="absolute top-3.5 right-3.5 h-1.5 w-1.5 rounded-full border border-[#5af2cf] shadow-[0_0_0_2px_rgba(90,242,207,0.12)]"></span>
                        <textarea
                          v-model="prompt"
                          ref="promptInput"
                          class="w-full bg-transparent border-0 focus:outline-none focus:ring-0 text-[14px] leading-[1.6] text-white placeholder-white/55 resize-none min-h-[38px] max-h-[160px] overflow-y-hidden"
                        placeholder="Reply..."
                        aria-label="Prompt input"
                        rows="1"
                        @keydown.enter.exact.prevent="handleSend"
                        @input="resizePrompt"
                      ></textarea>
                      <div class="flex flex-wrap items-center justify-between gap-3 text-white/75">
                        <div class="flex flex-wrap items-center gap-2">
                          <button
                            class="h-9 w-9 rounded-full border border-white/12 bg-white/5 hover:bg-white/10 transition flex items-center justify-center"
                              aria-label="Attach"
                              @click="openFilePicker"
                            >
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14m-7-7h14" />
                              </svg>
                            </button>
                            <div class="h-9 w-9 rounded-full border border-white/12 bg-white/5 flex items-center justify-center text-white/70">
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l2.5 2.5" />
                                <circle cx="12" cy="12" r="8.5" stroke-width="2" />
                              </svg>
                            </div>
                            <div class="flex items-center gap-1.5">
                              <button
                                class="px-2.5 h-8 rounded-full border text-[11px] font-semibold transition"
                                :class="dataSources.project_db ? 'bg-purple-700 text-white border-purple-500/60' : 'bg-white/5 border-white/12 text-white/60'"
                                type="button"
                                @click="toggleDataSource('project_db')"
                              >
                                Project DB
                              </button>
                              <button
                                class="px-2.5 h-8 rounded-full border text-[11px] font-semibold transition"
                                :class="dataSources.code_db ? 'bg-purple-700 text-white border-purple-500/60' : 'bg-white/5 border-white/12 text-white/60'"
                                type="button"
                                @click="toggleDataSource('code_db')"
                              >
                                Code DB
                              </button>
                              <button
                                class="px-2.5 h-8 rounded-full border text-[11px] font-semibold transition"
                                :class="dataSources.coop_manual ? 'bg-purple-700 text-white border-purple-500/60' : 'bg-white/5 border-white/12 text-white/60'"
                                type="button"
                                @click="toggleDataSource('coop_manual')"
                              >
                                Coop Manual
                              </button>
                            </div>
                          </div>
                          <div class="flex items-center gap-3">
                            <button
                              class="px-3.5 h-9 rounded-full bg-white/5 border border-white/12 hover:bg-white/10 transition text-[12px] font-semibold flex items-center gap-1.5"
                              type="button"
                              @click="cycleModel"
                              :title="`Model: ${selectedModel}`"
                            >
                              <span class="text-white/85">{{ selectedModel }}</span>
                              <svg class="w-3 h-3 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                              </svg>
                            </button>
                            <button
                              class="h-9 w-9 rounded-full flex items-center justify-center text-white flex-shrink-0 transition"
                              :class="(prompt.trim() || attachments.length) && !isSending ? 'bg-[#6b21a8] hover:bg-[#7c2cc7]' : 'bg-[#6b21a8]/50 cursor-not-allowed'"
                              aria-label="Send"
                              @click="handleSend"
                              :disabled="isSending || (!prompt.trim() && !attachments.length)"
                            >
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>

                      <div v-if="tags.length" class="flex flex-wrap items-center gap-2 text-[11px] text-white/50 pl-1">
                        <span
                          v-for="tag in tags"
                          :key="tag"
                          class="px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/75 tracking-[0.14em] uppercase"
                        >
                          {{ tag }}
                        </span>
                        <span class="ml-auto">Shift + Enter for newline</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div v-else-if="activePage === 'settings'" class="flex-1 min-h-0 overflow-hidden">
            <SettingsView />
          </div>

          <div v-else-if="activePage === 'work'" class="flex-1 min-h-0 overflow-hidden">
            <WorkView />
          </div>

          <div v-else-if="activePage === 'timesheet'" class="flex-1 min-h-0 overflow-hidden">
            <TimesheetView :initial-section="timesheetSection" />
          </div>

          <div v-else-if="activePage === 'todo'" class="flex-1 min-h-0 overflow-hidden">
            <TodoListView />
          </div>

          <div v-else-if="activePage === 'discussion'" class="flex-1 min-h-0 overflow-hidden">
            <DiscussionView />
          </div>
        </div>
      </main>
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        accept="image/*"
        multiple
        @change="handleFileChange"
      />
    </div>
    <div
      v-if="deleteDialog.open && deleteTarget"
      class="fixed inset-0 z-30 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
    >
      <div class="w-full max-w-md bg-[#111] border border-white/10 rounded-2xl shadow-2xl p-6 space-y-4">
        <div class="space-y-2">
          <p class="text-2xl font-semibold text-white">Delete chat?</p>
          <p class="text-sm text-white/75">
            This will delete <span class="font-semibold text-white">{{ deleteTarget.title }}</span>.
          </p>
          <p v-if="!canDeleteTarget" class="text-xs text-red-300">At least one conversation must remain.</p>
        </div>
        <div class="flex justify-end gap-2">
          <button
            class="px-4 py-2 rounded-full bg-white/5 border border-white/15 text-white/85 hover:bg-white/10 transition"
            @click="closeDeleteDialog"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 rounded-full bg-red-600 text-white font-semibold hover:bg-red-700 transition disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!canDeleteTarget"
            @click="performDeleteConversation"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: false
})

import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import FolderIcon from '~/components/icons/FolderIcon.vue'
import ChatIcon from '~/components/icons/ChatIcon.vue'
import GearIcon from '~/components/icons/GearIcon.vue'
import ClockIcon from '~/components/icons/ClockIcon.vue'
import ClipboardIcon from '~/components/icons/ClipboardIcon.vue'
import WorkView from '~/components/views/WorkView.vue'
import TimesheetView from '~/components/views/TimesheetView.vue'
import TodoListView from '~/components/views/TodoListView.vue'
import DiscussionView from '~/components/views/DiscussionView.vue'
import SettingsView from '~/components/views/SettingsView.vue'
import { useChat } from '~/composables/useChat'
import { useSmartChat } from '~/composables/useSmartChat'
import { useMessageFormatter } from '~/composables/useMessageFormatter'

type ChatEntry = {
  role: 'user' | 'assistant'
  content: string
  attachments?: string[]
}

type Conversation = {
  id: string
  title: string
  short: string
  time: string
  section: string
  sessionId: string
  chatLog: ChatEntry[]
}

const STORAGE_KEY = 'workspace-memory-v1'

const WorkIcon = defineComponent({
  name: 'WorkGlyph',
  setup() {
    return () =>
      h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
        h('rect', { x: '4', y: '7', width: '16', height: '11', rx: '2' }),
        h('path', { d: 'M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2' })
      ])
  }
})

const TodoIcon = defineComponent({
  name: 'TodoGlyph',
  setup() {
    return () =>
      h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2' }, [
        h('rect', { x: '4', y: '4', width: '16', height: '16', rx: '2' }),
        h('path', { d: 'M8 12l3 3 5-6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
      ])
  }
})

const railIcons = [
  { id: 'home', component: FolderIcon, label: 'Home' },
  { id: 'work', component: WorkIcon, label: 'Work' },
  { id: 'timesheet', component: ClockIcon, label: 'Timeline' },
  { id: 'todo', component: TodoIcon, label: 'To-Do List' },
  { id: 'discussion', component: ChatIcon, label: 'Discussion' },
  { id: 'settings', component: GearIcon, label: 'Settings' }
]

const availableModels = ['gpt-4o-120b', 'gpt-4o-mini']
const selectedModel = ref(availableModels[0])
const activePage = ref<'home' | 'settings' | 'work' | 'timesheet' | 'todo' | 'discussion'>('home')
const activeRail = computed(() => {
  return railIcons.some(icon => icon.id === activePage.value) ? activePage.value : 'home'
})
const userName = 'Zaryab'
const greetingTime = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Morning'
  if (hour < 18) return 'Afternoon'
  return 'Evening'
})
const greetingMessage = computed(() => `${greetingTime.value}, ${userName}`)
const timesheetSection = ref<'employees' | 'projects' | 'projectInsights' | 'employeeInsights' | 'nonDigital' | 'settings'>('employees')
const timesheetMenuOpen = ref(false)
let timesheetMenuTimer: ReturnType<typeof setTimeout> | null = null
const hoveredSimpleMenu = ref<string | null>(null)
let simpleMenuTimer: ReturnType<typeof setTimeout> | null = null
const renamingConversationId = ref<string | null>(null)
const renameDraft = ref('')
const renameInputRefs: Record<string, HTMLInputElement | null> = {}
const timesheetMenuItems = [
  { id: 'employees', label: 'Employees', icon: '👤' },
  { id: 'projects', label: 'Projects', icon: '📁' },
  { id: 'projectInsights', label: 'Project Insights', icon: '📈' },
  { id: 'employeeInsights', label: 'Employee Insights', icon: '📊' },
  { id: 'nonDigital', label: 'Daily Tasks', icon: '📝' },
  { id: 'settings', label: 'Settings', icon: '⚙️' }
] as const
const search = ref('')
const prompt = ref('')
const promptInput = ref<HTMLTextAreaElement | null>(null)
const tags = ref(['missile.ai'])
const chatContainer = ref<HTMLElement | null>(null)
const isSending = ref(false)
const attachments = ref<{ name: string; base64: string }[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const contextMenuRef = ref<HTMLElement | null>(null)
const { formatMessageText } = useMessageFormatter()
const { sendChatMessageStream } = useChat()
const { sendSmartMessage } = useSmartChat()
type DataSources = { project_db: boolean; code_db: boolean; coop_manual: boolean }
const dataSources = ref<DataSources>({
  project_db: true,
  code_db: true,
  coop_manual: true
})
type AgentLog = { id: string; thinking: string; timestamp: Date }
const agentLogs = ref<AgentLog[]>([])
const showScrollToBottom = ref(false)
const contextMenu = ref<{ visible: boolean; x: number; y: number; convId: string | null }>({
  visible: false,
  x: 0,
  y: 0,
  convId: null
})
const deleteDialog = ref<{ open: boolean; convId: string | null }>({
  open: false,
  convId: null
})

const defaultConversations: Conversation[] = [
  { id: 'conv-1', title: 'Submarine Simulation Refinement', short: 'Submarine Sim...', time: '52m ago', section: 'Today', sessionId: 'session-1', chatLog: [] },
  { id: 'conv-2', title: 'CFD Simulation Setup Review', short: 'CFD Setup Review', time: '1h ago', section: 'Today', sessionId: 'session-2', chatLog: [] },
  { id: 'conv-3', title: 'Calculating Reynolds number', short: 'Reynolds number', time: '2h ago', section: 'Today', sessionId: 'session-3', chatLog: [] },
  { id: 'conv-4', title: 'CFD Mesh Creation Request', short: 'CFD Mesh Request', time: '2h ago', section: 'Today', sessionId: 'session-4', chatLog: [] },
  { id: 'conv-5', title: 'Python Conversion: Knots to Mach', short: 'Knots to Mach', time: '3h ago', section: 'Today', sessionId: 'session-5', chatLog: [] },
  { id: 'conv-6', title: 'Submarine Simulation Refinement', short: 'Submarine Sim...', time: '5h ago', section: 'Today', sessionId: 'session-6', chatLog: [] },
  { id: 'conv-7', title: 'CFD Simulation for Car Model', short: 'Car CFD Sim', time: '6h ago', section: 'Today', sessionId: 'session-7', chatLog: [] },
  { id: 'conv-8', title: 'Ahmed Body Mesh Generation', short: 'Ahmed Mesh Gen', time: '6h ago', section: 'Today', sessionId: 'session-8', chatLog: [] },
  { id: 'conv-9', title: 'CFD Simulation Request follow-up', short: 'CFD follow-up', time: 'Yesterday', section: 'Yesterday', sessionId: 'session-9', chatLog: [] },
  { id: 'conv-10', title: 'Mesh Setup for Y+ Target', short: 'Y+ Target mesh', time: 'Nov 24', section: 'This Month', sessionId: 'session-10', chatLog: [] },
  { id: 'conv-11', title: 'Workspace Inquiry and Mapping', short: 'Workspace inquiry', time: 'Nov 24', section: 'This Month', sessionId: 'session-11', chatLog: [] },
  { id: 'conv-12', title: 'Available Tools Inquiry', short: 'Tools inquiry', time: 'Nov 19', section: 'This Month', sessionId: 'session-12', chatLog: [] },
  { id: 'conv-13', title: 'Mesh Setup for Geometry', short: 'Geometry mesh', time: 'Nov 19', section: 'This Month', sessionId: 'session-13', chatLog: [] },
  { id: 'conv-14', title: 'Mesh Refinement Zone Design', short: 'Refinement zone', time: 'Nov 19', section: 'This Month', sessionId: 'session-14', chatLog: [] }
]

const conversations = ref<Conversation[]>([...defaultConversations])

const sectionOrder = ['Today', 'Yesterday', 'This Month']
const activeConversationId = ref(conversations.value[0]?.id || '')

const activeConversation = computed(() => conversations.value.find(conv => conv.id === activeConversationId.value) || null)
const activeChatLog = computed(() => activeConversation.value?.chatLog ?? [])
const deleteTarget = computed(() => {
  if (!deleteDialog.value.convId) return null
  return conversations.value.find(conv => conv.id === deleteDialog.value.convId) || null
})
const canDeleteTarget = computed(() => conversations.value.length > 1)

const filteredConversationSections = computed(() => {
  const term = search.value.trim().toLowerCase()
  const filtered = conversations.value.filter(conv => {
    if (!term) return true
    return conv.title.toLowerCase().includes(term) || conv.short.toLowerCase().includes(term)
  })

  return sectionOrder
    .map(section => ({
      title: section,
      items: filtered.filter(conv => conv.section === section)
    }))
    .filter(section => section.items.length)
})

function scrollToBottom(smooth = false) {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
    }
  })
}

function handleChatScroll() {
  const el = chatContainer.value
  if (!el) return
  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
  showScrollToBottom.value = distanceFromBottom > 180
}

function saveMemory() {
  if (typeof window === 'undefined') return
  try {
    const payload = {
      conversations: conversations.value,
      activeConversationId: activeConversationId.value,
      tags: tags.value,
      selectedModel: selectedModel.value,
      dataSources: dataSources.value
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch (error) {
    console.warn('Unable to save workspace memory', error)
  }
}

function loadMemory() {
  if (typeof window === 'undefined') return
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed.conversations)) {
      conversations.value = parsed.conversations
    }
    if (parsed.activeConversationId) {
      activeConversationId.value = parsed.activeConversationId
    }
    if (Array.isArray(parsed.tags)) {
      tags.value = parsed.tags
    }
    if (typeof parsed.selectedModel === 'string' && availableModels.includes(parsed.selectedModel)) {
      selectedModel.value = parsed.selectedModel
    }
    if (parsed.dataSources) {
      dataSources.value = {
        project_db: parsed.dataSources.project_db ?? true,
        code_db: parsed.dataSources.code_db ?? true,
        coop_manual: parsed.dataSources.coop_manual ?? true
      }
    }
    const hasActive = conversations.value.some(conv => conv.id === activeConversationId.value)
    if (!hasActive) {
      activeConversationId.value = conversations.value[0]?.id || ''
    }
    if (!conversations.value.length) {
      conversations.value = [...defaultConversations]
      activeConversationId.value = conversations.value[0]?.id || ''
    }
  } catch (error) {
    console.warn('Unable to load workspace memory, using defaults', error)
  }
}

watch(
  () => activeChatLog.value.length,
  () => {
    scrollToBottom()
  }
)

watch(activeConversationId, () => {
  prompt.value = ''
  attachments.value = []
  nextTick(resizePrompt)
  scrollToBottom()
})

onMounted(() => {
  loadMemory()
  chatContainer.value?.addEventListener('scroll', handleChatScroll)
  handleChatScroll()
  document.addEventListener('click', handleGlobalClick)
  nextTick(resizePrompt)
})

watch(
  [conversations, activeConversationId, tags, selectedModel],
  () => saveMemory(),
  { deep: true }
)

watch(prompt, () => {
  nextTick(resizePrompt)
})

onBeforeUnmount(() => {
  chatContainer.value?.removeEventListener('scroll', handleChatScroll)
  document.removeEventListener('click', handleGlobalClick)
})

function setActivePage(id: string) {
  activePage.value = id as typeof activePage.value
}

function setActiveRail(id: string) {
  setActivePage(id)
}

function openTimesheetMenu() {
  if (timesheetMenuTimer) clearTimeout(timesheetMenuTimer)
  timesheetMenuOpen.value = true
}

function closeTimesheetMenu() {
  if (timesheetMenuTimer) clearTimeout(timesheetMenuTimer)
  timesheetMenuTimer = setTimeout(() => {
    timesheetMenuOpen.value = false
  }, 120)
}

function handleTimesheetNav(section: typeof timesheetSection.value) {
  timesheetSection.value = section
  activePage.value = 'timesheet'
  timesheetMenuOpen.value = false
}

function showSimpleMenu(id: string) {
  if (simpleMenuTimer) clearTimeout(simpleMenuTimer)
  hoveredSimpleMenu.value = id
}

function hideSimpleMenu() {
  if (simpleMenuTimer) clearTimeout(simpleMenuTimer)
  simpleMenuTimer = setTimeout(() => {
    hoveredSimpleMenu.value = null
  }, 120)
}

function setRenameInputRef(id: string, el: HTMLInputElement | null) {
  if (!el) {
    delete renameInputRefs[id]
  } else {
    renameInputRefs[id] = el
  }
}

function startRename(convId: string) {
  const convo = conversations.value.find(conv => conv.id === convId)
  if (!convo) return
  renamingConversationId.value = convId
  renameDraft.value = convo.title
  closeContextMenu()
  nextTick(() => {
    renameInputRefs[convId]?.focus()
    renameInputRefs[convId]?.select()
  })
}

function cancelRename() {
  renamingConversationId.value = null
  renameDraft.value = ''
}

function confirmRename(convId: string) {
  if (renamingConversationId.value !== convId) return
  const convo = conversations.value.find(conv => conv.id === convId)
  if (!convo) return cancelRename()
  const newTitle = renameDraft.value.trim()
  if (!newTitle || newTitle === convo.title) return cancelRename()
  convo.title = newTitle
  convo.short = shortenTitle(newTitle)
  convo.time = 'Just now'
  touchConversation(convo.id)
  cancelRename()
}

function cycleModel() {
  const currentIndex = availableModels.indexOf(selectedModel.value)
  const nextIndex = (currentIndex + 1) % availableModels.length
  selectedModel.value = availableModels[nextIndex]
}

function startNewConversation() {
  const newId = `conv-${Date.now()}`
  const title = `New Agent ${conversations.value.length + 1}`
  const newConversation: Conversation = {
    id: newId,
    title,
    short: shortenTitle(title),
    time: 'Just now',
    section: 'Today',
    sessionId: newId,
    chatLog: []
  }
  conversations.value = [newConversation, ...conversations.value]
  activeConversationId.value = newId
  activePage.value = 'home'
  prompt.value = ''
  attachments.value = []
}

function selectConversation(id: string) {
  if (activeConversationId.value === id) return
  activeConversationId.value = id
  activePage.value = 'home'
  prompt.value = ''
  closeContextMenu()
}

function handleTagClick(tag: string) {
  prompt.value = tag
}

function removeTag(tag: string) {
  tags.value = tags.value.filter(t => t !== tag)
}

function openFilePicker() {
  fileInput.value?.click()
}

function shortenTitle(title: string) {
  return title.length > 26 ? `${title.slice(0, 23)}...` : title
}

function convertFileToBase64(file: File): Promise<{ name: string; base64: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      const base64 = dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl
      resolve({ name: file.name, base64 })
    }
    reader.onerror = () => reject(new Error('Unable to read file'))
    reader.readAsDataURL(file)
  })
}

async function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  if (!files.length) return

  try {
    const converted = await Promise.all(files.map(file => convertFileToBase64(file)))
    attachments.value.push(...converted)
  } catch (error) {
    console.error('Failed to read attachments', error)
  } finally {
    // Allow selecting the same file again later
    target.value = ''
  }
}

function removeAttachment(idx: number) {
  attachments.value.splice(idx, 1)
}

function toggleDataSource(key: keyof DataSources) {
  dataSources.value[key] = !dataSources.value[key]
}

function resizePrompt() {
  const el = promptInput.value
  if (!el) return
  const maxHeight = 180
  el.style.height = 'auto'
  const next = Math.min(el.scrollHeight, maxHeight)
  el.style.height = `${next}px`
  el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden'
}

function touchConversation(convId: string) {
  const idx = conversations.value.findIndex(conv => conv.id === convId)
  if (idx === -1) return
  const [conv] = conversations.value.splice(idx, 1)
  conv.time = 'Just now'
  conv.section = 'Today'
  conversations.value = [conv, ...conversations.value]
}

async function handleSend() {
  const hasMessage = prompt.value.trim().length > 0
  const hasAttachments = attachments.value.length > 0
  if ((!hasMessage && !hasAttachments) || isSending.value) return

  const conversation = activeConversation.value
  if (!conversation) return

  const message = hasMessage ? prompt.value.trim() : 'What is shown in these attachments?'
  const attachmentNames = attachments.value.map(file => file.name)
  const imagesBase64 = attachments.value.length ? attachments.value.map(file => file.base64) : undefined

  conversation.chatLog.push({
    role: 'user',
    content: message,
    attachments: attachmentNames.length ? attachmentNames : undefined
  })

  prompt.value = ''
  attachments.value = []
  touchConversation(conversation.id)
  isSending.value = true
  scrollToBottom()

  try {
    // Initial routing (matches legacy SmartChatPanel behavior)
    const smartResp = await sendSmartMessage(message, {
      sessionId: conversation.sessionId,
      dataSources: dataSources.value,
      images_base64: imagesBase64
    })

    let gotResponse = false
    let streamError: Error | null = null

    await sendChatMessageStream(
      message,
      conversation.sessionId,
      imagesBase64,
      dataSources.value,
      {
        onLog: log => {
          console.log('Thinking log:', log)
          agentLogs.value.unshift({
            id: `log-${Date.now()}`,
            thinking: log.message,
            timestamp: new Date()
          })
        },
        onComplete: result => {
          const finalAnswer = result.reply || result.message || 'No response generated.'
          conversation.chatLog.push({ role: 'assistant', content: formatMessageText(finalAnswer) })
          gotResponse = true
          scrollToBottom(true)
        },
        onError: error => {
          streamError = error
        }
      }
    )

    if (streamError) {
      throw streamError
    }

    if (!gotResponse) {
      const fallback = smartResp?.message || smartResp?.reply || 'No response generated.'
      conversation.chatLog.push({ role: 'assistant', content: formatMessageText(fallback) })
      scrollToBottom(true)
    }
  } catch (error: any) {
    console.error('Send failed', error)
    conversation.chatLog.push({ role: 'assistant', content: 'Sorry, something went wrong sending that message.' })
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

function handleUpgrade() {
  alert('Upgrade options are coming soon.')
}

function renameConversation(convId: string) {
  startRename(convId)
}

function openContextMenu(event: MouseEvent, convId: string) {
  event.stopPropagation()
  closeContextMenu()
  const parentRect = (event.currentTarget as HTMLElement).closest('aside')?.getBoundingClientRect()
  const x = parentRect ? event.clientX - parentRect.left : event.clientX
  const y = parentRect ? event.clientY - parentRect.top : event.clientY
  const menuWidth = 180
  const menuHeight = 96
  const boundsWidth = parentRect ? parentRect.width : window.innerWidth
  const boundsHeight = parentRect ? parentRect.height : window.innerHeight
  const clampedX = Math.max(8, Math.min(x, boundsWidth - menuWidth - 8))
  const clampedY = Math.max(8, Math.min(y, boundsHeight - menuHeight - 8))
  contextMenu.value = { visible: true, x: clampedX, y: clampedY, convId }
}

function closeContextMenu() {
  contextMenu.value = { visible: false, x: 0, y: 0, convId: null }
}

function handleGlobalClick(event: MouseEvent) {
  if (!contextMenu.value.visible) return
  if (event.button === 2) return
  const menuEl = contextMenuRef.value
  if (menuEl && menuEl.contains(event.target as Node)) return
  closeContextMenu()
}

function openDeleteDialog(convId: string) {
  closeContextMenu()
  deleteDialog.value = { open: true, convId }
}

function closeDeleteDialog() {
  deleteDialog.value = { open: false, convId: null }
}

function deleteConversation(convId: string) {
  const convo = conversations.value.find(conv => conv.id === convId)
  if (!convo) return
  conversations.value = conversations.value.filter(conv => conv.id !== convId)
  if (activeConversationId.value === convId) {
    activeConversationId.value = conversations.value[0]?.id || ''
    prompt.value = ''
    attachments.value = []
  }
}

function performDeleteConversation() {
  const convId = deleteDialog.value.convId
  if (!convId) return closeDeleteDialog()
  if (!canDeleteTarget.value) {
    return closeDeleteDialog()
  }
  deleteConversation(convId)
  closeDeleteDialog()
}
</script>

<style scoped>
.custom-scroll::-webkit-scrollbar {
  width: 8px;
}
.custom-scroll::-webkit-scrollbar-track {
  background: #0d0d0d;
}
.custom-scroll::-webkit-scrollbar-thumb {
  background: #1f1f1f;
  border-radius: 8px;
}
.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: #2a2a2a;
}

.workspace-shell {
  min-width: 0;
  height: calc(100vh - 36px);
}

.workspace-root {
  font-size: 12px;
}

.workspace-main {
  min-width: 0;
}

.conversation-sidebar {
  min-width: 200px;
}

.workspace-root {
  font-size: 11px;
  height: 100vh;
  overflow: hidden;
}

.chat-frame {
  width: min(100%, 960px);
  margin: 0 auto;
  height: 100%;
  max-height: 100%;
}

@media (max-width: 1024px) {
  .workspace-shell {
    flex-direction: column;
  }
  .conversation-sidebar {
    width: 100%;
    order: 2;
    border-right: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    max-height: 45vh;
  }
  .workspace-main {
    order: 1;
  }
}

@media (max-width: 640px) {
  .workspace-main > div {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .conversation-sidebar {
    max-height: 50vh;
  }
}

@media (min-width: 1440px) {
  .workspace-root {
    font-size: 12px;
  }
}
</style>
