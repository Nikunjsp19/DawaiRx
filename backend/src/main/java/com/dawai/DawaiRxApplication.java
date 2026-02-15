package com.dawai;

import com.dawai.controller.AdminController;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import(AdminController.class)
public class DawaiRxApplication {

    public static void main(String[] args) {
        SpringApplication.run(DawaiRxApplication.class, args);
    }
}
