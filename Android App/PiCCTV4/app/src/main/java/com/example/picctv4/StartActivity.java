package com.example.picctv4;


import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.AsyncTask;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.net.UnknownHostException;

public class StartActivity extends AppCompatActivity {
    private String host = "192.168.0.8";
    private int TCPport = 7000;
    private String uName = "jh2735";
    private String pwd = "1234";

    private EditText textViewUserName;
    private EditText textViewPassword;

    private EditText textViewIP;
    private EditText textViewPort;
    private boolean success;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_start);
        //Get the last IP and port value, and show them
        // get the textView object
        textViewIP = (EditText) findViewById(R.id.systemIP);
        textViewPort = (EditText) findViewById(R.id.systemPort);
        textViewPassword = (EditText) findViewById(R.id.systmePassword);
        textViewUserName = (EditText) findViewById(R.id.systemUserName);

        // set default host and port
        textViewUserName.setText(uName);
        textViewPassword.setText(pwd);
        // set default host and port
        textViewIP.setText(host);
        textViewPort.setText(String.valueOf(TCPport));
        success = false;
        Button buttonEnter = (Button) findViewById(R.id.enter);
        buttonEnter.setOnClickListener(

                (x) -> {
                    uName = textViewUserName.getText().toString();
                    pwd = textViewPassword.getText().toString();
                    host = textViewIP.getText().toString();
                    TCPport = Integer.valueOf(textViewPort.getText().toString());

                    if (uName == null || uName.length() == 0 || pwd == null || pwd.length() == 0) {
                        showToast("please fill all blanks");
                        return;
                    }else{
                        StartActivity.Sender sender = new  StartActivity.Sender();
                        sender.host = host;
                        sender.port = TCPport;
                        sender.msg = "Check:"+uName+":"+pwd;
                        sender.type = "login";
                        sender.execute();
                        long timeInit = System.currentTimeMillis();
                        while(System.currentTimeMillis() - timeInit<3000){
                            if (success){
                                Intent startMainActivityIntent = new Intent(StartActivity.this, MainActivity.class);
                                startActivity(startMainActivityIntent);
                                finish();
                            }
                        }
                    }
                });

    }
    private void showToast (String Str) {
        Toast.makeText(this, Str, Toast.LENGTH_SHORT).show();
        Toast.makeText(this, Str, Toast.LENGTH_SHORT).show();
    }
    class Sender extends AsyncTask<Void,Void,Void> {
        Socket s;
        PrintWriter pw;
        String msg;
        String type;
        BufferedReader bufferedReader;
        String host;
        int port;

        @SuppressLint("SetTextI18n")
        @Override
        protected Void doInBackground(Void...params){
            try {
                s = new Socket(host, port);
                pw = new PrintWriter(s.getOutputStream());
                pw.write(msg);
                pw.flush();
                bufferedReader = new BufferedReader(new InputStreamReader(s.getInputStream()));
                String msg2 = bufferedReader.readLine();

                switch (type) {
                    case "login":
                        if (msg2!=null && msg2.equals("Success")) {
                            success = true;
                        }else{

                        }
                        break;
                }

                bufferedReader.close();
                pw.close();
                s.close();
            } catch (UnknownHostException e) {
                System.out.println("Fail");
                e.printStackTrace();
            } catch (IOException e) {
                System.out.println("Fail");
                e.printStackTrace();
            }
            return null;
        }
    }
}





