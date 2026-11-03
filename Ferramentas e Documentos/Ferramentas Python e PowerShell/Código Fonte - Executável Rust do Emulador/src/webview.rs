use tao::dpi::LogicalSize;
use tao::event::{Event, WindowEvent};
use tao::event_loop::{ControlFlow, EventLoop, EventLoopBuilder, EventLoopProxy};
use tao::window::WindowBuilder;
use wry::{WebContext, WebViewBuilder};

pub enum UserEvent {
    ShowDashboard,
    #[allow(dead_code)]
    HideDashboard,
    RequestShutdownConfirmation,
    ExitProcess,
    ToggleFullscreen,
    ToggleCompactMode,
}

pub struct WebViewApp {
    event_loop: EventLoop<UserEvent>,
    proxy: EventLoopProxy<UserEvent>,
}

fn prepare_clean_appdata_webview_dir() -> std::path::PathBuf {
    // Remove legacy local WebView2 directory next to the executable if present
    let _ = std::fs::remove_dir_all("Aion Classic - EMULADOR.exe.WebView2");

    let appdata_base = std::env::var_os("LOCALAPPDATA")
        .or_else(|| std::env::var_os("APPDATA"))
        .map(std::path::PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);

    let webview_data_dir = appdata_base.join("AionClassicEmulador").join("WebView2");
    if webview_data_dir.exists() {
        let _ = std::fs::remove_dir_all(&webview_data_dir);
    }
    let _ = std::fs::create_dir_all(&webview_data_dir);
    std::env::set_var("WEBVIEW2_USER_DATA_FOLDER", &webview_data_dir);
    webview_data_dir
}

impl WebViewApp {
    pub fn new() -> Self {
        let event_loop = EventLoopBuilder::<UserEvent>::with_user_event().build();
        let proxy = event_loop.create_proxy();
        Self { event_loop, proxy }
    }

    pub fn get_proxy(&self) -> EventLoopProxy<UserEvent> {
        self.proxy.clone()
    }

    pub fn run(
        self,
        url: String,
        cleanup_on_exit: impl Fn() + Send + Sync + 'static,
    ) {
        let webview_data_dir = prepare_clean_appdata_webview_dir();
        let mut web_context = WebContext::new(Some(webview_data_dir));

        let window = WindowBuilder::new()
            .with_title("Aion Classic - EMULADOR")
            .with_inner_size(LogicalSize::new(1440.0, 900.0))
            .with_min_inner_size(LogicalSize::new(1024.0, 680.0))
            .build(&self.event_loop)
            .expect("Failed to build window");

        let webview = match WebViewBuilder::with_web_context(&mut web_context)
            .with_url(&url)
            .build(&window)
        {
            Ok(wv) => Some(wv),
            Err(e) => {
                let _ = std::fs::write("logs/webview_error.log", format!("WebView Error: {:?}", e));
                eprintln!("WARN: [WebView] Failed to initialize WebView2: {}", e);
                None
            }
        };

        window.set_focus();

        let mut is_compact = false;

        self.event_loop.run(move |event, _, control_flow| {
            let _keep_alive = (&webview, &web_context);
            *control_flow = ControlFlow::Wait;

            match event {
                Event::UserEvent(UserEvent::ToggleCompactMode) => {
                    is_compact = !is_compact;
                    if is_compact {
                        window.set_always_on_top(true);
                        window.set_resizable(false);
                        window.set_inner_size(LogicalSize::new(460.0, 310.0));
                        if let Some(wv) = &webview {
                            let _ = wv.evaluate_script("if(typeof setCompactMode === 'function') setCompactMode(true);");
                        }
                    } else {
                        window.set_always_on_top(false);
                        window.set_resizable(true);
                        window.set_inner_size(LogicalSize::new(1440.0, 900.0));
                        if let Some(wv) = &webview {
                            let _ = wv.evaluate_script("if(typeof setCompactMode === 'function') setCompactMode(false);");
                        }
                    }
                    window.set_visible(true);
                    window.set_focus();
                }
                Event::UserEvent(UserEvent::ShowDashboard) => {
                    window.set_visible(true);
                    window.set_focus();
                }
                Event::UserEvent(UserEvent::HideDashboard) => {
                    window.set_visible(false);
                }
                Event::UserEvent(UserEvent::ToggleFullscreen) => {
                    let is_fs = window.fullscreen().is_some();
                    if is_fs {
                        window.set_fullscreen(None);
                    } else {
                        window.set_fullscreen(Some(tao::window::Fullscreen::Borderless(None)));
                    }
                }
                Event::UserEvent(UserEvent::RequestShutdownConfirmation) => {
                    window.set_visible(true);
                    window.set_focus();
                    if let Some(wv) = &webview {
                        let _ = wv.evaluate_script("if(typeof requestAppShutdownConfirmation === 'function') requestAppShutdownConfirmation(); else if(typeof openShutdownModal === 'function') openShutdownModal();");
                    }
                }
                Event::UserEvent(UserEvent::ExitProcess) => {
                    cleanup_on_exit();
                    *control_flow = ControlFlow::Exit;
                }
                Event::WindowEvent {
                    event: WindowEvent::CloseRequested,
                    ..
                } => {
                    // Do NOT immediately close or hide the window!
                    // Prompt the user for confirmation and show shutdown progress
                    window.set_visible(true);
                    window.set_focus();
                    if let Some(wv) = &webview {
                        let _ = wv.evaluate_script("if(typeof requestAppShutdownConfirmation === 'function') requestAppShutdownConfirmation(); else if(typeof openShutdownModal === 'function') openShutdownModal();");
                    }
                }
                Event::WindowEvent {
                    event: WindowEvent::Destroyed,
                    ..
                } => {
                    let _ = std::fs::write("logs/exit_reason.log", "Window Destroyed received\n");
                }
                _ => (),
            }
        });
    }
}
