package com.example.picctv4;

// author: jie he (jh2735) & yuchong geng (yg534)

import androidx.annotation.RequiresApi;
import androidx.appcompat.app.AppCompatActivity;

import android.annotation.SuppressLint;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.net.UnknownHostException;

public class MainActivity extends AppCompatActivity {
    private EditText usernameEditText;
    private EditText passwordEditText;
    private TextView statusTextView;
    private String uName = "jh2735";
    private String pwd = "1234";
    private TextView doorStatusTextView;
    private boolean success = false;
    private boolean doorOpen = false;

    private WebView webView;
    @RequiresApi(api = Build.VERSION_CODES.LOLLIPOP)
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);


        statusTextView = findViewById(R.id.status);
        doorStatusTextView = findViewById(R.id.door);

        usernameEditText = findViewById(R.id.username);
        passwordEditText = findViewById(R.id.password);
        final Button loginButton = findViewById(R.id.loginbtn);
        final Button doorButton = findViewById(R.id.doorbtn);


        statusTextView.setText("Login Success");
        usernameEditText.setText(uName, TextView.BufferType.NORMAL);
        passwordEditText.setText(pwd,TextView.BufferType.NORMAL);
        doorStatusTextView.setText("Door Closed");


        webView = (WebView) findViewById(R.id.webView);
        // to make the webview adapt to the screen
        WebSettings settings = webView.getSettings();
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(true);
        MediaPlayer mediaPlayer = new MediaPlayer();
        mediaPlayer.setAudioAttributes(
                new AudioAttributes.Builder()
                        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .build()
        );
        try {
            mediaPlayer.setDataSource("http://192.168.1.12:8000/rapi.mp3");
            mediaPlayer.prepare();
        } catch (IOException e) {
            e.printStackTrace();
        }
        //  might take long! (for buffering, etc)
        mediaPlayer.start();

        // --------
        webView.setWebViewClient(new WebViewClient());
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.setOverScrollMode(WebView.OVER_SCROLL_NEVER);
        webView.loadUrl("http://192.168.1.12:9000/index.html");

        loginButton.setOnClickListener(
                (x)->{
                    if(!success){
                        uName = usernameEditText.getText().toString();
                        pwd = passwordEditText.getText().toString();
                        if (uName == null || uName.length() == 0 || pwd == null || pwd.length() == 0) {
                            showToast("please fill all blanks");
                            return;
                        }else{
                            Sender sender = new Sender();
                            sender.msg = "Check:"+uName+":"+pwd;
                            sender.type = "login";
                            sender.execute();
                        }
                    }else{
                        statusTextView.setText("Login Success!");
                        showToast("You already Log in !");
                    }

                }
        );

        doorButton.setOnClickListener(
                (x)->{
                    Sender sender = new Sender();
                    sender.msg = "Door Open";
                    sender.type = "doorOpen";
                    sender.execute();
                }
        );

    }

    private void showToast(String Str) {
        Toast.makeText(this, Str, Toast.LENGTH_SHORT).show();
        Toast.makeText(this, Str, Toast.LENGTH_SHORT).show();
    }

    class Sender extends AsyncTask<Void,Void,Void> {
        Socket s;
        PrintWriter pw;
        String msg;
        String type;
        BufferedReader bufferedReader;
        @SuppressLint("SetTextI18n")
        @Override
        protected Void doInBackground(Void...params){
            try {
                s = new Socket("192.168.1.12", 7000);
                pw = new PrintWriter(s.getOutputStream());
                pw.write(msg);
                pw.flush();
                bufferedReader = new BufferedReader(new InputStreamReader(s.getInputStream()));
                String msg2 = bufferedReader.readLine();

                switch (type) {
                    case "login":
                        if (msg2!=null && msg2.equals("Success")) {
                            success = true;
                            statusTextView.setText("Login Success");
                            showToast("Login Success");

                        }else{
                            statusTextView.setText("Not Login In");
                            showToast("Login Fail");
                        }
                        break;
                    case "doorOpen":
                        if (msg2!=null && msg2.equals("Success")) {
                            doorOpen = true;
                            doorStatusTextView.setText("Door Open");
                        }
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