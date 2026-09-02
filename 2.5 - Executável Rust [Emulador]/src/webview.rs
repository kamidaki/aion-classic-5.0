use tao::dpi::LogicalSize;
use tao::event::{Event, WindowEvent};
use tao::event_loop::{ControlFlow, EventLoop, EventLoopBuilder, EventLoopProxy};
use tao::window::WindowBuilder;
use wry::WebViewBuilder;

pub enum UserEvent {
    ShowDashboard,
    #[allow(dead_code)]
    HideDashboard,
    RequestShutdown,
    ToggleFullscreen,
}

pub struct WebViewApp {
    event_loop: EventLoop<UserEvent>,
    proxy: EventLoopProxy<UserEvent>,
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
        shutdown_trigger: impl Fn() + Send + Sync + 'static,
    ) {
        let window = WindowBuilder::new()
            .with_title("Aion Classic - Classic Emu")
            .with_inner_size(LogicalSize::new(1440.0, 900.0))
            .with_min_inner_size(LogicalSize::new(1024.0, 680.0))
            .build(&self.event_loop)
            .expect("Failed to build window");

        let webview = match WebViewBuilder::new().with_url(&url).build(&window) {
            Ok(wv) => Some(wv),
            Err(e) => {
                let _ = std::fs::write("logs/webview_error.log", format!("WebView Error: {:?}", e));
                eprintln!("WARN: [WebView] Failed to initialize WebView2: {}", e);
                None
            }
        };

        window.set_focus();

        self.event_loop.run(move |event, _, control_flow| {
            let _keep_alive = &webview;
            *control_flow = ControlFlow::Wait;

            match event {
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
                Event::UserEvent(UserEvent::RequestShutdown) => {
                    let _ = std::fs::write("logs/exit_reason.log", "RequestShutdown received\n");
                    shutdown_trigger();
                    *control_flow = ControlFlow::Exit;
                }
                Event::WindowEvent {
                    event: WindowEvent::CloseRequested,
                    ..
                } => {
                    // Hide to system tray instead of killing backend
                    window.set_visible(false);
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
